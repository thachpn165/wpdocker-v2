-- waf/lua/rules/protect_sensitive_files.lua

local _M = {}

-- Danh sách các đường dẫn/tập tin nhạy cảm không nên truy cập trực tiếp
-- (dựa theo OWASP CRS - lfi-os-files.data, restricted-files.data, v.v.)
local sensitive_paths = {
    ".htaccess", ".htdigest", ".htpasswd", ".addressbook", ".aptitude/config", ".aws/", ".azure/", ".bash_", ".bashrc",
    ".cache/notify-osd.log", ".config/", ".cshrc", ".docker", ".drush/", ".env", ".eslintignore", ".fbcindex", ".forward",
    ".gitattributes", ".gitconfig", ".gnupg/", ".google_authenticator", ".hplip/hplip.conf", ".ksh_history", ".lesshst",
    ".lftp/", ".lhistory", ".lighttpdpassword", ".lldb-history", ".local/share/mc/", ".lynx_cookies", ".my.cnf",
    ".mysql_history", ".nano_history", ".node_repl_history", ".npmrc", ".nsconfig", ".nsr", ".oh-my-", ".password-store",
    ".pearrc", ".pgpass", ".php_history", ".pinerc", ".pki/", ".proclog", ".procmailrc", ".profile", ".psql_history",
    ".python_history", ".rediscli_history", ".rhistory", ".rhosts", ".selected_editor", ".sh_history", ".sqlite_history",
    ".snap/", ".ssh/", ".subversion/", ".tconn/", ".tcshrc", ".tmux.conf", ".tor/", ".vagrant.d/", ".vidalia/", ".vim/",
    ".viminfo", ".vimrc", ".vscode", ".www_acl", ".wwwacl", ".Xauthority", ".yarnrc", ".zhistory", ".zsh_history",
    ".zshenv", ".zshrc", "/.git/", "/.gitignore", "/.hg/", "/.hgignore", "/.svn/", "/auth.json", "wp-config.php",
    "wp-config.bak", "wp-config.old", "wp-config.temp", "wp-config.tmp", "wp-config.txt", "/config/config.yml",
    "/config/config_dev.yml", "/config/config_prod.yml", "/config/config_test.yml", "/config/parameters.yml",
    "/config/routing.yml", "/config/security.yml", "/config/services.yml", "/sites/default/default.settings.php",
    "/sites/default/settings.php", "/sites/default/settings.local.php", "/config/config.php",
    "/config/settings.inc.php", "/app/config/parameters.php", "/app/etc/local.xml", "/sftp-config.json",
    "/Web.config", "/package.json", "/package-lock.json", "/npm-shrinkwrap.json", "/gruntfile.js", "/npm-debug.log",
    "/ormconfig.json", "/tsconfig.json", "/webpack.config.js", "/yarn.lock", "/composer.json", "/composer.lock",
    "/packages.json", "/.DS_Store", "/.ws_ftp.ini", ".idea", "nbproject/", "bower.json", ".bowerrc", ".eslintrc",
    ".jshintrc", ".gitlab-ci.yml", ".travis.yml", "database.yml", "Dockerfile", ".php_cs.dist", ".phpcs.xml", "phpcs.xml",
    ".phpcs.xml.dist", "phpcs.xml.dist", "Desktop.ini", "Thumbs.db", ".user.ini", "php.ini", "weblogic.xml",
    "soapConfig.xml", "php_error.log", "php_errors.log", "WEB-INF/", "sslvpn_websession", "BlockCypher.log",
    "config.inc.php", "config.sample.php", "defaults.inc.php", "sendgrid.env", ".fish", "fish_variables",
    "ldap-authentication-report.csv", "user_secrets.yml", "secrets.json", "compose.yml", "compose.yaml",
    "cloud-config.yml", "proc/", "proc/0", "proc/1", "proc/2", "proc/3", "proc/4", "proc/5", "proc/6", "proc/7", "proc/8",
    "proc/9", "proc/acpi", "proc/asound", "proc/bootconfig", "proc/buddyinfo", "proc/bus", "proc/cgroups", "proc/cmdline",
    "proc/config.gz", "proc/consoles", "proc/cpuinfo", "proc/crypto", "proc/devices", "proc/diskstats", "proc/dma",
    "proc/docker", "proc/driver", "proc/dynamic_debug", "proc/execdomains", "proc/fb", "proc/filesystems", "proc/fs",
    "proc/interrupts", "proc/iomem", "proc/ioports", "proc/ipmi", "proc/irq", "proc/kallsyms", "proc/kcore", "proc/key-users",
    "proc/keys", "proc/kmsg", "proc/kpagecgroup", "proc/kpagecount", "proc/kpageflags", "proc/latency_stats", "proc/loadavg",
    "proc/locks", "proc/mdstat", "proc/meminfo", "proc/misc", "proc/modules", "proc/mounts", "proc/mpt", "proc/mtd",
    "proc/mtrr", "proc/net", "proc/pagetypeinfo", "proc/partitions", "proc/pressure", "proc/sched_debug",
    "proc/schedstat", "proc/scsi", "proc/self", "proc/slabinfo", "proc/softirqs", "proc/stat", "proc/swaps", "proc/sys",
    "proc/sysrq-trigger", "proc/sysvipc", "proc/thread-self", "proc/timer_list", "proc/timer_stats", "proc/tty",
    "proc/uptime", "proc/version", "proc/version_signature", "proc/vmallocinfo", "proc/vmstat", "proc/zoneinfo",
    "sys/block", "sys/bus", "sys/class", "sys/dev", "sys/devices", "sys/firmware", "sys/fs", "sys/hypervisor",
    "sys/kernel", "sys/module", "sys/power"
}

function _M.run()
    local uri = ngx.var.request_uri or ""
    for _, pattern in ipairs(sensitive_paths) do
        if uri:lower():find(pattern:lower(), 1, true) then
            ngx.log(ngx.ERR, "[WAF] 🚫 Access to sensitive file or path detected: ", uri)
            return ngx.exit(403)
        end
    end
end

return _M