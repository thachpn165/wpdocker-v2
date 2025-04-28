-- waf/lua/rules/restricted-upload.lua

local _M = {}

-- Danh sách các tên file bị hạn chế không được phép upload (theo OWASP CRS restricted-files.data)
local restricted_filenames = {
    ".DS_Store", ".addressbook", ".bash_", ".bashrc", ".bowerrc", ".cshrc", ".docker", ".env", ".eslintignore", ".eslintrc",
    ".fbcindex", ".forward", ".gitattributes", ".gitconfig", ".gitignore", ".gitlab-ci.yml", ".google_authenticator", ".hgignore",
    ".htaccess", ".htdigest", ".htpasswd", ".idea", ".jshintrc", ".ksh_history", ".lesshst", ".lhistory", ".lighttpdpassword",
    ".lldb-history", ".lynx_cookies", ".my.cnf", ".mysql_history", ".nano_history", ".node_repl_history", ".nsconfig", ".nsr",
    ".oh-my-", ".password-store", ".pearrc", ".pgpass", ".php_cs.dist", ".php_history", ".phpcs.xml", ".phpcs.xml.dist", ".pinerc",
    ".proclog", ".procmailrc", ".profile", ".psql_history", ".python_history", ".rediscli_history", ".rhistory", ".rhosts",
    ".sh_history", ".sqlite_history", ".tcshrc", ".travis.yml", ".user.ini", ".viminfo", ".vimrc", ".ws_ftp.ini", ".www_acl",
    ".wwwacl", ".xauthority", ".zhistory", ".zsh_history", ".zshrc",
    "Desktop.ini", "Dockerfile", "Thumbs.db", "Web.config", "acpi", "asound", "auth.json", "bootconfig", "bower.json",
    "buddyinfo", "cgroups", "cmdline", "composer.json", "composer.lock", "config.gz", "config.inc.php", "config.php",
    "config.sample.php", "config.yml", "config_dev.yml", "config_prod.yml", "config_test.yml", "cpuinfo", "database.yml",
    "defaults.inc.php", "default.settings.php", "diskstats", "dynamic_debug", "execdomains", "filesystems", "gruntfile.js",
    "hplip.conf", "hypervisor", "iomem", "ioports", "ipmi", "kallsyms", "kcore", "key-users", "kmsg", "kpagecgroup",
    "kpagecount", "kpageflags", "latency_stats", "loadavg", "local.xml", "mdstat", "meminfo", "mtrr", "notify-osd.log",
    "npm-debug.log", "npm-shrinkwrap.json", "ormconfig.json", "package-lock.json", "package.json", "packages.json",
    "pagetypeinfo", "parameters.php", "parameters.yml", "php.ini", "php_error.log", "php_errors.log", "phpcs.xml",
    "phpcs.xml.dist", "routing.yml", "sched_debug", "schedstat", "security.yml", "services.yml", "settings.inc.php",
    "settings.local.php", "settings.php", "sftp-config.json", "slabinfo", "soapConfig.xml", "softirqs", "sslvpn_websession",
    "sysrq-trigger", "sysvipc", "thread-self", "timer_list", "timer_stats", "tsconfig.json", "version_signature",
    "vmallocinfo", "vmstat", "weblogic.xml", "webpack.config.js", "wp-config.bak", "wp-config.old", "wp-config.php",
    "wp-config.temp", "wp-config.tmp", "wp-config.txt", "yarn.lock", "zoneinfo"
}

function _M.run()
    local uri = ngx.var.request_uri or ""
    local method = ngx.req.get_method()

    if method ~= "POST" and method ~= "PUT" then
        return
    end

    for _, filename in ipairs(restricted_filenames) do
        if uri:find(filename, 1, true) then
            ngx.log(ngx.ERR, "[WAF] 🚫 Attempt to upload restricted file: ", filename)
            return ngx.exit(403)
        end
    end
end

return _M
