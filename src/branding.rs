//! Thinking Fish Assist branding and baked-in server configuration.
//!
//! Thinking Fish Assist is a rebranded build of RustDesk (AGPL-3.0). Everything
//! that makes this build "ours" rather than stock RustDesk starts here, so an
//! upstream merge only has to keep this module wired in.
//!
//! What it does, once, at process start (from `load_custom_client`):
//!   * sets the internal app name. It has no spaces on purpose: upstream uses it
//!     for install folders, the Windows service name, launchd plist names, the
//!     config directory and the URI scheme, all of which assume
//!     alphanumerics only. People see `DISPLAY_NAME` instead (see lang.rs and
//!     the Flutter `kAppDisplayName`).
//!   * pins our ID/relay server, its public key and the API server as
//!     *override* settings. Override means a customer cannot change or clear
//!     them in Settings > Network, so a fresh install works with no setup and
//!     cannot be pointed at someone else's server by accident.
//!
//! The server values can be replaced at compile time (TFA_RENDEZVOUS_SERVER,
//! TFA_RS_PUB_KEY, TFA_API_SERVER) for a staging build; the defaults below are
//! production. None of them is a secret: the public key is public by design.

use hbb_common::config::{self, keys};

/// Internal name: folders, service names, URI scheme. Alphanumerics only.
pub const APP_NAME: &str = "ThinkingFishAssist";
/// What people see.
pub const DISPLAY_NAME: &str = "Thinking Fish Assist";
/// Our product version (upstream's protocol version stays in `crate::VERSION`,
/// because peers compare it to decide which features the other side supports).
pub const PRODUCT_VERSION: &str = "1.0.1";
/// The upstream RustDesk release this build is based on.
pub const UPSTREAM_VERSION: &str = "1.4.9";
pub const SOURCE_URL: &str = "https://github.com/thinking-fish/thinking-fish-assist";
pub const SUPPORT_URL: &str = "https://thinking.fish/assist";
pub const PRIVACY_URL: &str = "https://thinking.fish/privacy";

pub const RENDEZVOUS_SERVER: &str = match option_env!("TFA_RENDEZVOUS_SERVER") {
    Some(v) => v,
    None => "assist.thinkingfish.com",
};
pub const RS_PUB_KEY: &str = match option_env!("TFA_RS_PUB_KEY") {
    Some(v) => v,
    None => "MUzGM83Kvm7xbcjeWSfkpVPrbS81h3MUstgdc2Y5fuU=",
};
pub const API_SERVER: &str = match option_env!("TFA_API_SERVER") {
    Some(v) => v,
    None => "https://assist.thinkingfish.com",
};

/// Apply the branding. Must run before anything reads `Config`, because the
/// config file path is derived from the app name.
pub fn apply() {
    *config::APP_NAME.write().unwrap() = APP_NAME.to_owned();

    let mut o = config::OVERWRITE_SETTINGS.write().unwrap();
    o.insert(
        keys::OPTION_CUSTOM_RENDEZVOUS_SERVER.to_owned(),
        RENDEZVOUS_SERVER.to_owned(),
    );
    o.insert(keys::OPTION_KEY.to_owned(), RS_PUB_KEY.to_owned());
    o.insert(keys::OPTION_API_SERVER.to_owned(), API_SERVER.to_owned());
    // The relay address comes from our ID server (hbbs -r), so it is not pinned here.
    // Never offer RustDesk's own updates: they would replace this build with stock
    // RustDesk. (Upstream already skips the check for a renamed app; this makes sure.)
    o.insert(keys::OPTION_ALLOW_AUTO_UPDATE.to_owned(), "N".to_owned());
    drop(o);
    config::OVERWRITE_LOCAL_SETTINGS
        .write()
        .unwrap()
        .insert(keys::OPTION_ENABLE_CHECK_UPDATE.to_owned(), "N".to_owned());
}
