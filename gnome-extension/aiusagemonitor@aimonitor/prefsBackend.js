import Gio from 'gi://Gio';

export function runBackendAsync(extensionPath, args, callback) {
    const proc = new Gio.Subprocess({
        argv: ['python3', `${extensionPath}/scripts/fetch_all_usage.py`, ...args],
        flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
    });
    proc.init(null);
    proc.communicate_utf8_async(null, null, (self, result) => {
        try {
            const [, stdout, stderr] = self.communicate_utf8_finish(result);
            if (self.get_successful() && stdout?.trim()) {
                callback(null, JSON.parse(stdout.trim()));
                return;
            }
            callback(new Error(stderr?.trim() || 'Backend command failed'));
        } catch (error) {
            callback(error);
        }
    });
}
