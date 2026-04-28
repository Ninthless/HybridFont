#include <android/log.h>
#include <fcntl.h>
#include <stdarg.h>
#include <sys/stat.h>
#include <unistd.h>

#include <cstdio>
#include <cstring>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>

#include "zygisk.hpp"

namespace {

constexpr const char *tag = "HybridFontZygisk";

zygisk::Api *zygisk_api = nullptr;
std::unordered_map<std::string, int> font_fds;

int (*orig_open)(const char *, int, ...) = nullptr;
int (*orig_open64)(const char *, int, ...) = nullptr;
int (*orig_openat)(int, const char *, int, ...) = nullptr;
int (*orig_openat64)(int, const char *, int, ...) = nullptr;
FILE *(*orig_fopen)(const char *, const char *) = nullptr;
FILE *(*orig_fopen64)(const char *, const char *) = nullptr;
int (*orig_access)(const char *, int) = nullptr;
int (*orig_faccessat)(int, const char *, int, int) = nullptr;
int (*orig_stat)(const char *, struct stat *) = nullptr;
int (*orig_lstat)(const char *, struct stat *) = nullptr;

std::string basename_of(std::string_view path) {
    auto pos = path.find_last_of('/');
    if (pos == std::string_view::npos) {
        return std::string(path);
    }
    return std::string(path.substr(pos + 1));
}

bool is_font_path(std::string_view path) {
    return path.starts_with("/system/fonts/") || path.starts_with("/system/product/fonts/");
}

int replacement_fd(const char *path) {
    if (path == nullptr || !is_font_path(path)) {
        return -1;
    }
    auto it = font_fds.find(basename_of(path));
    if (it == font_fds.end()) {
        return -1;
    }
    return dup(it->second);
}

int open_with_original(int (*fn)(const char *, int, ...), const char *path, int flags, va_list args) {
    if ((flags & O_CREAT) != 0) {
        auto mode = static_cast<mode_t>(va_arg(args, int));
        return fn(path, flags, mode);
    }
    return fn(path, flags);
}

int openat_with_original(int (*fn)(int, const char *, int, ...), int dirfd, const char *path, int flags, va_list args) {
    if ((flags & O_CREAT) != 0) {
        auto mode = static_cast<mode_t>(va_arg(args, int));
        return fn(dirfd, path, flags, mode);
    }
    return fn(dirfd, path, flags);
}

int hooked_open(const char *path, int flags, ...) {
    if ((flags & (O_WRONLY | O_RDWR | O_CREAT | O_TRUNC | O_APPEND)) == 0) {
        int fd = replacement_fd(path);
        if (fd >= 0) {
            return fd;
        }
    }
    va_list args;
    va_start(args, flags);
    int result = open_with_original(orig_open, path, flags, args);
    va_end(args);
    return result;
}

int hooked_open64(const char *path, int flags, ...) {
    if ((flags & (O_WRONLY | O_RDWR | O_CREAT | O_TRUNC | O_APPEND)) == 0) {
        int fd = replacement_fd(path);
        if (fd >= 0) {
            return fd;
        }
    }
    va_list args;
    va_start(args, flags);
    int result = open_with_original(orig_open64, path, flags, args);
    va_end(args);
    return result;
}

int hooked_openat(int dirfd, const char *path, int flags, ...) {
    if ((flags & (O_WRONLY | O_RDWR | O_CREAT | O_TRUNC | O_APPEND)) == 0) {
        int fd = replacement_fd(path);
        if (fd >= 0) {
            return fd;
        }
    }
    va_list args;
    va_start(args, flags);
    int result = openat_with_original(orig_openat, dirfd, path, flags, args);
    va_end(args);
    return result;
}

int hooked_openat64(int dirfd, const char *path, int flags, ...) {
    if ((flags & (O_WRONLY | O_RDWR | O_CREAT | O_TRUNC | O_APPEND)) == 0) {
        int fd = replacement_fd(path);
        if (fd >= 0) {
            return fd;
        }
    }
    va_list args;
    va_start(args, flags);
    int result = openat_with_original(orig_openat64, dirfd, path, flags, args);
    va_end(args);
    return result;
}

FILE *hooked_fopen(const char *path, const char *mode) {
    if (mode != nullptr && mode[0] == 'r') {
        int fd = replacement_fd(path);
        if (fd >= 0) {
            return fdopen(fd, mode);
        }
    }
    return orig_fopen(path, mode);
}

FILE *hooked_fopen64(const char *path, const char *mode) {
    if (mode != nullptr && mode[0] == 'r') {
        int fd = replacement_fd(path);
        if (fd >= 0) {
            return fdopen(fd, mode);
        }
    }
    return orig_fopen64(path, mode);
}

int hooked_access(const char *path, int mode) {
    int fd = replacement_fd(path);
    if (fd >= 0) {
        close(fd);
        return 0;
    }
    return orig_access(path, mode);
}

int hooked_faccessat(int dirfd, const char *path, int mode, int flags) {
    int fd = replacement_fd(path);
    if (fd >= 0) {
        close(fd);
        return 0;
    }
    return orig_faccessat(dirfd, path, mode, flags);
}

int hooked_stat(const char *path, struct stat *buffer) {
    int fd = replacement_fd(path);
    if (fd >= 0) {
        int result = fstat(fd, buffer);
        close(fd);
        return result;
    }
    return orig_stat(path, buffer);
}

int hooked_lstat(const char *path, struct stat *buffer) {
    int fd = replacement_fd(path);
    if (fd >= 0) {
        int result = fstat(fd, buffer);
        close(fd);
        return result;
    }
    return orig_lstat(path, buffer);
}

void open_font(int module_dir, const char *name) {
    std::string path = "fonts/";
    path += name;
    int fd = openat(module_dir, path.c_str(), O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        return;
    }
    zygisk_api->exemptFd(fd);
    font_fds[name] = fd;
}

void load_fonts() {
    int module_dir = zygisk_api->getModuleDir();
    if (module_dir < 0) {
        return;
    }
    const char *names[] = {
        "Roboto-Regular.ttf",
        "RobotoStatic-Regular.ttf",
        "Roboto-Italic.ttf",
        "Roboto-Thin.ttf",
        "Roboto-ThinItalic.ttf",
        "Roboto-Light.ttf",
        "Roboto-LightItalic.ttf",
        "Roboto-Medium.ttf",
        "Roboto-MediumItalic.ttf",
        "Roboto-Bold.ttf",
        "Roboto-BoldItalic.ttf",
        "Roboto-Black.ttf",
        "Roboto-BlackItalic.ttf",
        "SysSans-Hans-Regular.ttf",
        "NotoSansCJKsc-Regular.otf",
        "NotoSansCJKsc-Thin.otf",
        "NotoSansCJKsc-Light.otf",
        "NotoSansCJKsc-DemiLight.otf",
        "NotoSansCJKsc-Medium.otf",
        "NotoSansCJKsc-Bold.otf",
        "NotoSansCJKsc-Black.otf",
        "NotoSansCJK-VF.ttf",
        "NotoSansCJKsc-VF.ttf",
        "DroidSansFallback.ttf",
        "DroidSansFallbackFull.ttf",
    };
    for (const char *name : names) {
        open_font(module_dir, name);
    }
    close(module_dir);
}

bool should_hook_elf(std::string_view path) {
    if (path.empty() || path == "[anon:linker_alloc]") {
        return false;
    }
    if (path.find("/system/") == std::string_view::npos && path.find("/apex/") == std::string_view::npos) {
        return false;
    }
    return path.ends_with(".so") || path.find("/app_process") != std::string_view::npos;
}

void register_hooks_for(dev_t dev, ino_t inode) {
    zygisk_api->pltHookRegister(dev, inode, "open", reinterpret_cast<void *>(hooked_open), reinterpret_cast<void **>(&orig_open));
    zygisk_api->pltHookRegister(dev, inode, "open64", reinterpret_cast<void *>(hooked_open64), reinterpret_cast<void **>(&orig_open64));
    zygisk_api->pltHookRegister(dev, inode, "openat", reinterpret_cast<void *>(hooked_openat), reinterpret_cast<void **>(&orig_openat));
    zygisk_api->pltHookRegister(dev, inode, "openat64", reinterpret_cast<void *>(hooked_openat64), reinterpret_cast<void **>(&orig_openat64));
    zygisk_api->pltHookRegister(dev, inode, "fopen", reinterpret_cast<void *>(hooked_fopen), reinterpret_cast<void **>(&orig_fopen));
    zygisk_api->pltHookRegister(dev, inode, "fopen64", reinterpret_cast<void *>(hooked_fopen64), reinterpret_cast<void **>(&orig_fopen64));
    zygisk_api->pltHookRegister(dev, inode, "access", reinterpret_cast<void *>(hooked_access), reinterpret_cast<void **>(&orig_access));
    zygisk_api->pltHookRegister(dev, inode, "faccessat", reinterpret_cast<void *>(hooked_faccessat), reinterpret_cast<void **>(&orig_faccessat));
    zygisk_api->pltHookRegister(dev, inode, "stat", reinterpret_cast<void *>(hooked_stat), reinterpret_cast<void **>(&orig_stat));
    zygisk_api->pltHookRegister(dev, inode, "lstat", reinterpret_cast<void *>(hooked_lstat), reinterpret_cast<void **>(&orig_lstat));
}

void register_hooks() {
    FILE *maps = fopen("/proc/self/maps", "r");
    if (maps == nullptr) {
        return;
    }
    char line[4096];
    std::unordered_set<std::string> seen;
    while (fgets(line, sizeof(line), maps) != nullptr) {
        char path[3072] = {};
        unsigned long start = 0;
        unsigned long end = 0;
        unsigned long offset = 0;
        unsigned int major = 0;
        unsigned int minor = 0;
        unsigned long inode = 0;
        char perms[5] = {};
        int matched = sscanf(line, "%lx-%lx %4s %lx %x:%x %lu %3071s", &start, &end, perms, &offset, &major, &minor, &inode, path);
        if (matched != 8 || inode == 0 || !should_hook_elf(path)) {
            continue;
        }
        if (!seen.insert(path).second) {
            continue;
        }
        struct stat st = {};
        if (stat(path, &st) != 0) {
            continue;
        }
        register_hooks_for(st.st_dev, st.st_ino);
    }
    fclose(maps);
}

class HybridFontModule : public zygisk::ModuleBase {
public:
    void onLoad(zygisk::Api *api, JNIEnv *) override {
        zygisk_api = api;
    }

    void preAppSpecialize(zygisk::AppSpecializeArgs *) override {
        install();
    }

    void preServerSpecialize(zygisk::ServerSpecializeArgs *) override {
        install();
    }

private:
    void install() {
        load_fonts();
        if (font_fds.empty()) {
            __android_log_print(ANDROID_LOG_WARN, tag, "no fonts loaded");
            return;
        }
        register_hooks();
        if (!zygisk_api->pltHookCommit()) {
            __android_log_print(ANDROID_LOG_WARN, tag, "plt hook commit failed");
        }
    }
};

} 

REGISTER_ZYGISK_MODULE(HybridFontModule)
