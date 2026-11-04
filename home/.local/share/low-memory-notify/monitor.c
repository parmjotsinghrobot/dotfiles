#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <spawn.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

extern char **environ;

static long long now_ms(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (long long)t.tv_sec * 1000 + t.tv_nsec / 1000000;
}

static bool notify(const char *title, const char *body) {
    char *args[] = {"notify-send", "--app-name=Memory monitor",
        "--urgency=critical", "--icon=dialog-warning",
        (char *)title, (char *)body, NULL};
    pid_t pid;
    int err = posix_spawnp(&pid, args[0], NULL, NULL, args, environ);
    if (err) {
        fprintf(stderr, "notify-send: %s\n", strerror(err));
        return false;
    }
    int status;
    while (waitpid(pid, &status, 0) < 0) {
        if (errno != EINTR) return false;
    }
    return WIFEXITED(status) && WEXITSTATUS(status) == 0;
}

static long available_kib(void) {
    FILE *f = fopen("/proc/meminfo", "r");
    if (!f) return -1;
    char line[256];
    long value = -1;
    while (fgets(line, sizeof(line), f)) {
        if (sscanf(line, "MemAvailable: %ld kB", &value) == 1) break;
    }
    fclose(f);
    return value;
}

static void check_memory(long kib, bool *warned) {
    if (kib < 0) return;
    if (kib >= 1310720) *warned = false;
    else if (kib < 1048576 && !*warned) {
        char body[160];
        snprintf(body, sizeof(body),
            "Only %ld MiB of RAM available (below 1 GiB).", kib / 1024);
        if (notify("Low memory", body)) *warned = true;
    }
}

/* Independently verify events against recent observed stall-counter growth.
 * This also rejects events caused by stale kernel trigger startup baselines. */
struct pressure_sample { long long ms; unsigned long long total; };
static struct pressure_sample samples[16];
static unsigned sample_count;

static bool pressure_confirmed(void) {
    FILE *f = fopen("/proc/pressure/memory", "r");
    if (!f) return false;
    char line[256];
    unsigned long long total = 0;
    bool found = false;
    while (fgets(line, sizeof(line), f)) {
        char *value = strstr(line, "total=");
        if (strncmp(line, "some ", 5) == 0 && value &&
            sscanf(value, "total=%llu", &total) == 1) {
            found = true;
            break;
        }
    }
    fclose(f);
    if (!found) return false;
    long long now = now_ms();
    bool confirmed = false;
    for (unsigned i = 0; i < sample_count; ++i) {
        if (now - samples[i].ms <= 2000 && total >= samples[i].total &&
            total - samples[i].total >= 200000) confirmed = true;
    }
    if (sample_count == 16) {
        memmove(samples, samples + 1, 15 * sizeof(*samples));
        --sample_count;
    }
    samples[sample_count++] = (struct pressure_sample){now, total};
    return confirmed;
}

static void pressure_event(long long now, long long *next_warning) {
    if (now < *next_warning) return;
    if (notify("Memory pressure detected",
        "Tasks stalled on memory for at least 200 ms within a 2-second window. "
        "Consider closing memory-heavy apps.")) {
        *next_warning = now + 60000;
    } else {
        *next_warning = now + 5000;
    }
}

int main(void) {
    int fd = open("/proc/pressure/memory", O_RDWR | O_NONBLOCK | O_CLOEXEC);
    if (fd < 0) {
        perror("open memory pressure monitor");
        return 1;
    }
    const char trigger[] = "some 200000 2000000";
    if (write(fd, trigger, sizeof(trigger)) != sizeof(trigger)) {
        perror("register memory pressure trigger");
        close(fd);
        return 1;
    }
    fprintf(stderr, "Monitoring available RAM every 1 second; memory pressure "
        "threshold 200 ms / 2 seconds; pressure alert cooldown 60 seconds.\n");
    struct pollfd pfd = {.fd = fd, .events = POLLPRI};
    bool warned = false;
    long long next_check = 0, next_pressure_warning = 0;
    for (;;) {
        long long now = now_ms();
        if (now >= next_check) {
            check_memory(available_kib(), &warned);
            (void)pressure_confirmed();
            next_check = now_ms() + 1000;
        }
        long long remaining = next_check - now_ms();
        int timeout = remaining > 0 ? (int)remaining : 0;
        int result = poll(&pfd, 1, timeout);
        if (result < 0) {
            if (errno == EINTR) continue;
            perror("poll memory pressure");
            return 1;
        }
        if (pfd.revents & (POLLERR | POLLHUP | POLLNVAL)) {
            fprintf(stderr, "Memory pressure monitor disconnected\n");
            return 1;
        }
        if (pfd.revents & POLLPRI) {
            if (pressure_confirmed()) {
                fprintf(stderr, "Confirmed memory pressure threshold event\n");
                pressure_event(now_ms(), &next_pressure_warning);
            } else {
                fprintf(stderr, "Ignored pressure event: recent stall counter below threshold\n");
            }
        }
    }
}
