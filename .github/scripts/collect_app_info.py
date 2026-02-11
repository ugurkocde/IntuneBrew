import json
import os
import requests
import re
import fileinput
from pathlib import Path
import subprocess
from datetime import datetime
import hashlib
import tempfile
from urllib.parse import urlparse, unquote


def get_filename_from_url(url, app_name=None, version=None, default_ext=".dmg"):
    """
    Extract a proper filename from a URL, handling query parameters and edge cases.

    Args:
        url: The download URL
        app_name: Optional app name to use if filename cannot be determined
        version: Optional version to include in generated filename
        default_ext: Default extension if none can be determined (default: .dmg)

    Returns:
        A proper filename with extension
    """
    # Parse the URL to get just the path (without query params or fragments)
    parsed = urlparse(url)
    path = unquote(parsed.path)

    # Get the basename from the path
    filename = os.path.basename(path)

    # Check if the filename has a valid extension
    valid_extensions = ['.dmg', '.pkg', '.zip', '.app', '.tar.gz', '.tar.xz', '.tar.bz2', '.tbz']
    has_valid_ext = any(filename.lower().endswith(ext) for ext in valid_extensions)

    # If no valid extension found, try to construct a proper filename
    if not has_valid_ext or not filename or filename in ['download', 'latest']:
        if app_name:
            # Construct filename from app name and version
            safe_name = app_name.replace(' ', '-')
            if version:
                filename = f"{safe_name}-{version}{default_ext}"
            else:
                filename = f"{safe_name}{default_ext}"
        else:
            # Fallback: use the original basename but add extension if missing
            if not filename or '?' in filename or filename in ['download', 'latest']:
                filename = f"download{default_ext}"
            elif '.' not in filename:
                filename = f"{filename}{default_ext}"

    return filename


# List of apps that should preserve their fileName field (not be overwritten)
preserve_filename_apps = [
    "tenable_nessus_agent"
]

# zip, tar etc
app_urls = [
    "https://formulae.brew.sh/api/cask/signal.json",
    "https://formulae.brew.sh/api/cask/medis.json",
    "https://formulae.brew.sh/api/cask/sourcetree.json",
    "https://formulae.brew.sh/api/cask/sequel-ace.json",
    "https://formulae.brew.sh/api/cask/textmate.json",
    "https://formulae.brew.sh/api/cask/free-ruler.json",
    "https://formulae.brew.sh/api/cask/superlist.json",
    "https://formulae.brew.sh/api/cask/viz.json",
    "https://formulae.brew.sh/api/cask/huggingchat.json",
    "https://formulae.brew.sh/api/cask/gather.json",
    "https://formulae.brew.sh/api/cask/flowvision.json",
    "https://formulae.brew.sh/api/cask/copyclip.json",
    "https://formulae.brew.sh/api/cask/batfi.json",
    "https://formulae.brew.sh/api/cask/bleunlock.json",
    "https://formulae.brew.sh/api/cask/loop.json",
    "https://formulae.brew.sh/api/cask/elgato-capture-device-utility.json",
    "https://formulae.brew.sh/api/cask/godspeed.json",
    "https://formulae.brew.sh/api/cask/hey.json",
    "https://formulae.brew.sh/api/cask/tex-live-utility.json",
    "https://formulae.brew.sh/api/cask/deskpad.json",
    "https://formulae.brew.sh/api/cask/windowkeys.json",
    "https://formulae.brew.sh/api/cask/huly.json",
    "https://formulae.brew.sh/api/cask/asset-catalog-tinkerer.json",
    "https://formulae.brew.sh/api/cask/forecast.json",
    "https://formulae.brew.sh/api/cask/last-window-quits.json",
    "https://formulae.brew.sh/api/cask/taskbar.json",
    "https://formulae.brew.sh/api/cask/superwhisper.json",
    "https://formulae.brew.sh/api/cask/notesollama.json",
    "https://formulae.brew.sh/api/cask/oversight.json",
    "https://formulae.brew.sh/api/cask/pronotes.json",
    "https://formulae.brew.sh/api/cask/hammerspoon.json",
    "https://formulae.brew.sh/api/cask/swift-shift.json",
    "https://formulae.brew.sh/api/cask/splice.json",
    "https://formulae.brew.sh/api/cask/screenfocus.json",
    "https://formulae.brew.sh/api/cask/teacode.json",
    "https://formulae.brew.sh/api/cask/alcove.json",
    "https://formulae.brew.sh/api/cask/abstract.json",
    "https://formulae.brew.sh/api/cask/macpass.json",
    "https://formulae.brew.sh/api/cask/marsedit.json",
    "https://formulae.brew.sh/api/cask/neofinder.json",
    "https://formulae.brew.sh/api/cask/netiquette.json",
    "https://formulae.brew.sh/api/cask/nova.json",
    "https://formulae.brew.sh/api/cask/overflow.json",
    "https://formulae.brew.sh/api/cask/platypus.json",
    "https://formulae.brew.sh/api/cask/plistedit-pro.json",
    "https://formulae.brew.sh/api/cask/principle.json",
    "https://formulae.brew.sh/api/cask/qlab.json",
    "https://formulae.brew.sh/api/cask/rode-connect.json",
    "https://formulae.brew.sh/api/cask/rode-central.json",
    "https://formulae.brew.sh/api/cask/sqlpro-for-mssql.json",
    "https://formulae.brew.sh/api/cask/sqlpro-for-postgres.json",
    "https://formulae.brew.sh/api/cask/sqlpro-for-mysql.json",
    "https://formulae.brew.sh/api/cask/sqlpro-for-sqlite.json",
    "https://formulae.brew.sh/api/cask/sqlpro-studio.json",
    "https://formulae.brew.sh/api/cask/silentknight.json",
    "https://formulae.brew.sh/api/cask/homerow.json",
    "https://formulae.brew.sh/api/cask/paintbrush.json",
    "https://formulae.brew.sh/api/cask/mattermost.json",
    "https://formulae.brew.sh/api/cask/flycut.json",
    "https://formulae.brew.sh/api/cask/sublime-merge.json",
    "https://formulae.brew.sh/api/cask/netnewswire.json",
    "https://formulae.brew.sh/api/cask/love.json",
    "https://formulae.brew.sh/api/cask/block-goose.json",
    "https://formulae.brew.sh/api/cask/espanso.json",
    "https://formulae.brew.sh/api/cask/shortcat.json",
    "https://formulae.brew.sh/api/cask/copilot-for-xcode.json",
    "https://formulae.brew.sh/api/cask/macs-fan-control.json",
    "https://formulae.brew.sh/api/cask/plex.json",
    "https://formulae.brew.sh/api/cask/macwhisper.json",
    "https://formulae.brew.sh/api/cask/reactotron.json",
    "https://formulae.brew.sh/api/cask/macdown.json",
    "https://formulae.brew.sh/api/cask/middleclick.json",
    "https://formulae.brew.sh/api/cask/openmtp.json",
    "https://formulae.brew.sh/api/cask/pearcleaner.json",
    "https://formulae.brew.sh/api/cask/notunes.json",
    "https://formulae.brew.sh/api/cask/keycastr.json",
    "https://formulae.brew.sh/api/cask/itsycal.json",
    "https://formulae.brew.sh/api/cask/vimr.json",
    "https://formulae.brew.sh/api/cask/audio-hijack.json",
    "https://formulae.brew.sh/api/cask/visual-studio-code.json",
    "https://formulae.brew.sh/api/cask/microsoft-azure-storage-explorer.json",
    "https://formulae.brew.sh/api/cask/figma.json",
    "https://formulae.brew.sh/api/cask/postman.json",
    "https://formulae.brew.sh/api/cask/fantastical.json",
    "https://formulae.brew.sh/api/cask/iterm2.json",
    "https://formulae.brew.sh/api/cask/sublime-text.json",
    "https://formulae.brew.sh/api/cask/vivaldi.json",
    "https://formulae.brew.sh/api/cask/github.json",
    "https://formulae.brew.sh/api/cask/transmit.json",
    "https://formulae.brew.sh/api/cask/1password.json",
    "https://formulae.brew.sh/api/cask/alfred.json",
    "https://formulae.brew.sh/api/cask/asana.json",
    "https://formulae.brew.sh/api/cask/arc.json",
    "https://formulae.brew.sh/api/cask/azure-data-studio.json",
    "https://formulae.brew.sh/api/cask/bartender.json",
    "https://formulae.brew.sh/api/cask/basecamp.json",
    "https://formulae.brew.sh/api/cask/domzilla-caffeine.json",
    "https://formulae.brew.sh/api/cask/claude.json",
    "https://formulae.brew.sh/api/cask/cursor.json",
    "https://formulae.brew.sh/api/cask/flux.json",
    "https://formulae.brew.sh/api/cask/gitkraken.json",
    "https://formulae.brew.sh/api/cask/godot.json",
    "https://formulae.brew.sh/api/cask/hp-easy-admin.json",
    "https://formulae.brew.sh/api/formula/vim.json",
    "https://formulae.brew.sh/api/cask/notion-calendar.json",
    "https://formulae.brew.sh/api/cask/ollama.json",
    "https://formulae.brew.sh/api/cask/pdf-expert.json",
    "https://formulae.brew.sh/api/cask/wine-stable.json",
    "https://formulae.brew.sh/api/cask/alt-tab.json",
    "https://formulae.brew.sh/api/cask/maccy.json",
    "https://formulae.brew.sh/api/cask/whatsapp.json",
    "https://formulae.brew.sh/api/cask/mitmproxy.json",
    "https://formulae.brew.sh/api/cask/telegram.json",
    "https://formulae.brew.sh/api/cask/jordanbaird-ice.json",
    "https://formulae.brew.sh/api/cask/appcleaner.json",
    "https://formulae.brew.sh/api/cask/cyberduck.json",
    "https://formulae.brew.sh/api/cask/logi-options+.json",
    "https://formulae.brew.sh/api/cask/mountain-duck.json",
    "https://formulae.brew.sh/api/cask/acorn.json",
    "https://formulae.brew.sh/api/cask/menubar-stats.json",
    "https://formulae.brew.sh/api/formula/neovim.json",
    "https://formulae.brew.sh/api/cask/sketch.json",
    "https://formulae.brew.sh/api/cask/jumpcut.json",
    "https://formulae.brew.sh/api/cask/daisydisk.json",
    "https://formulae.brew.sh/api/cask/cleanmymac.json",
    "https://formulae.brew.sh/api/cask/bettertouchtool.json",
    "https://formulae.brew.sh/api/cask/battle-net.json",
    "https://formulae.brew.sh/api/cask/betterzip.json",
    "https://formulae.brew.sh/api/cask/blip.json",
    "https://formulae.brew.sh/api/cask/boop.json",
    "https://formulae.brew.sh/api/cask/busycal.json",
    "https://formulae.brew.sh/api/cask/busycontacts.json",
    "https://formulae.brew.sh/api/cask/beeper.json",
    "https://formulae.brew.sh/api/cask/airfoil.json",
    "https://formulae.brew.sh/api/cask/angry-ip-scanner.json",
    "https://formulae.brew.sh/api/cask/home-assistant.json",
    "https://formulae.brew.sh/api/cask/hyper.json",
    "https://formulae.brew.sh/api/cask/fsmonitor.json",
    "https://formulae.brew.sh/api/cask/fission.json",
    "https://formulae.brew.sh/api/cask/geekbench.json",
    "https://formulae.brew.sh/api/cask/geekbench-ai.json",
    "https://formulae.brew.sh/api/cask/gemini.json",
    "https://formulae.brew.sh/api/cask/coderunner.json",
    "https://formulae.brew.sh/api/cask/devtoys.json",
    "https://formulae.brew.sh/api/cask/drivedx.json",
    "https://formulae.brew.sh/api/cask/dropshare.json",
    "https://formulae.brew.sh/api/cask/easyfind.json",
    "https://formulae.brew.sh/api/cask/beyond-compare.json",
    "https://formulae.brew.sh/api/cask/bettermouse.json",
    "https://formulae.brew.sh/api/cask/logitech-g-hub.json",
    "https://formulae.brew.sh/api/cask/jumpshare.json",
    "https://formulae.brew.sh/api/cask/keybase.json",
    "https://formulae.brew.sh/api/cask/keyclu.json",
    "https://formulae.brew.sh/api/formula/antigen.json",
    "https://formulae.brew.sh/api/cask/nucleo.json",
    "https://formulae.brew.sh/api/cask/spline.json",
    "https://formulae.brew.sh/api/cask/mac-mouse-fix.json",
    "https://formulae.brew.sh/api/cask/amazon-workspaces.json",
    "https://formulae.brew.sh/api/cask/propresenter.json",
    # New ZIP/Archive apps (batch 1 - 37 apps)
    "https://formulae.brew.sh/api/cask/affinity-designer.json",
    "https://formulae.brew.sh/api/cask/affinity-photo.json",
    "https://formulae.brew.sh/api/cask/affinity-publisher.json",
    "https://formulae.brew.sh/api/cask/carbon-copy-cloner.json",
    "https://formulae.brew.sh/api/cask/coconutbattery.json",
    "https://formulae.brew.sh/api/cask/dash.json",
    "https://formulae.brew.sh/api/cask/devonthink.json",
    "https://formulae.brew.sh/api/cask/element.json",
    "https://formulae.brew.sh/api/cask/forklift.json",
    "https://formulae.brew.sh/api/cask/front.json",
    "https://formulae.brew.sh/api/cask/fsnotes.json",
    "https://formulae.brew.sh/api/cask/gitbutler.json",
    "https://formulae.brew.sh/api/cask/glyphs.json",
    "https://formulae.brew.sh/api/cask/iconjar.json",
    "https://formulae.brew.sh/api/cask/imageoptim.json",
    "https://formulae.brew.sh/api/cask/jump-desktop.json",
    "https://formulae.brew.sh/api/cask/kaleidoscope.json",
    "https://formulae.brew.sh/api/cask/keyboard-maestro.json",
    "https://formulae.brew.sh/api/cask/knockknock.json",
    "https://formulae.brew.sh/api/cask/loopback.json",
    "https://formulae.brew.sh/api/cask/min.json",
    "https://formulae.brew.sh/api/cask/monodraw.json",
    "https://formulae.brew.sh/api/cask/orion.json",
    "https://formulae.brew.sh/api/cask/paste.json",
    "https://formulae.brew.sh/api/cask/popclip.json",
    "https://formulae.brew.sh/api/cask/rightfont.json",
    "https://formulae.brew.sh/api/cask/screens.json",
    "https://formulae.brew.sh/api/cask/soundsource.json",
    "https://formulae.brew.sh/api/cask/swinsian.json",
    "https://formulae.brew.sh/api/cask/the-unarchiver.json",
    "https://formulae.brew.sh/api/cask/tower.json",
    "https://formulae.brew.sh/api/cask/tripmode.json",
    "https://formulae.brew.sh/api/cask/tunnelbear.json",
    "https://formulae.brew.sh/api/cask/vmware-fusion.json",
    "https://formulae.brew.sh/api/cask/workflowy.json",
    "https://formulae.brew.sh/api/cask/yattee.json",
    "https://formulae.brew.sh/api/cask/yoink.json",
    # New ZIP/Archive apps (batch 2 - 33 apps)
    "https://formulae.brew.sh/api/cask/altair-graphql-client.json",
    "https://formulae.brew.sh/api/cask/castr.json",
    "https://formulae.brew.sh/api/cask/chromium.json",
    "https://formulae.brew.sh/api/cask/coherence-x.json",
    "https://formulae.brew.sh/api/cask/dockview.json",
    "https://formulae.brew.sh/api/cask/dropzone.json",
    "https://formulae.brew.sh/api/cask/ecamm-live.json",
    "https://formulae.brew.sh/api/cask/fastscripts.json",
    "https://formulae.brew.sh/api/cask/fluid.json",
    "https://formulae.brew.sh/api/cask/framer.json",
    "https://formulae.brew.sh/api/cask/graphiql.json",
    "https://formulae.brew.sh/api/cask/guitar-pro.json",
    "https://formulae.brew.sh/api/cask/heptabase.json",
    "https://formulae.brew.sh/api/cask/iconset.json",
    "https://formulae.brew.sh/api/cask/mailmate.json",
    "https://formulae.brew.sh/api/cask/mailspring.json",
    "https://formulae.brew.sh/api/cask/openinterminal.json",
    "https://formulae.brew.sh/api/cask/rambox.json",
    "https://formulae.brew.sh/api/cask/reflect.json",
    "https://formulae.brew.sh/api/cask/remnote.json",
    "https://formulae.brew.sh/api/cask/scrivener.json",
    "https://formulae.brew.sh/api/cask/scroll-reverser.json",
    "https://formulae.brew.sh/api/cask/superhuman.json",
    "https://formulae.brew.sh/api/cask/tabby.json",
    "https://formulae.brew.sh/api/cask/tidal.json",
    "https://formulae.brew.sh/api/cask/ubar.json",
    "https://formulae.brew.sh/api/cask/unclutter.json",
    "https://formulae.brew.sh/api/cask/unite.json",
    "https://formulae.brew.sh/api/cask/wezterm.json",
    "https://formulae.brew.sh/api/cask/whimsical.json",
    "https://formulae.brew.sh/api/cask/workspaces.json",
    "https://formulae.brew.sh/api/cask/zeplin.json",
    # New ZIP/Archive apps (batch 3 - 35 apps)
    "https://formulae.brew.sh/api/cask/alloy.json",
    "https://formulae.brew.sh/api/cask/altserver.json",
    "https://formulae.brew.sh/api/cask/amadeus-pro.json",
    "https://formulae.brew.sh/api/cask/amie.json",
    "https://formulae.brew.sh/api/cask/android-commandlinetools.json",
    "https://formulae.brew.sh/api/cask/android-platform-tools.json",
    "https://formulae.brew.sh/api/cask/appgrid.json",
    "https://formulae.brew.sh/api/cask/apptivate.json",
    "https://formulae.brew.sh/api/cask/aurora-hdr.json",
    "https://formulae.brew.sh/api/cask/backuploupe.json",
    "https://formulae.brew.sh/api/cask/battery-buddy.json",
    "https://formulae.brew.sh/api/cask/beardedspice.json",
    "https://formulae.brew.sh/api/cask/bitbar.json",
    "https://formulae.brew.sh/api/cask/boinc.json",
    "https://formulae.brew.sh/api/cask/caption.json",
    "https://formulae.brew.sh/api/cask/catch.json",
    "https://formulae.brew.sh/api/cask/chirp.json",
    "https://formulae.brew.sh/api/cask/choosy.json",
    "https://formulae.brew.sh/api/cask/cleartext.json",
    "https://formulae.brew.sh/api/cask/cloudytabs.json",
    "https://formulae.brew.sh/api/cask/colorsnapper.json",
    "https://formulae.brew.sh/api/cask/combine-pdfs.json",
    "https://formulae.brew.sh/api/cask/compositor.json",
    "https://formulae.brew.sh/api/cask/crossover.json",
    "https://formulae.brew.sh/api/cask/dash-dash.json",
    "https://formulae.brew.sh/api/cask/deepnest.json",
    "https://formulae.brew.sh/api/cask/devkinsta.json",
    "https://formulae.brew.sh/api/cask/devonagent.json",
    "https://formulae.brew.sh/api/cask/elan.json",
    "https://formulae.brew.sh/api/cask/electron.json",
    "https://formulae.brew.sh/api/cask/electron-fiddle.json",
    "https://formulae.brew.sh/api/cask/elgato-control-center.json",
    "https://formulae.brew.sh/api/cask/envkey.json",
    "https://formulae.brew.sh/api/cask/evkey.json",
    "https://formulae.brew.sh/api/cask/filebot.json",
    "https://formulae.brew.sh/api/cask/1password-cli.json",
    "https://formulae.brew.sh/api/cask/activedock.json",
    "https://formulae.brew.sh/api/cask/amethyst.json",
    "https://formulae.brew.sh/api/cask/antigravity.json",
    "https://formulae.brew.sh/api/cask/appium-inspector.json",
    "https://formulae.brew.sh/api/cask/backlog.json",
    "https://formulae.brew.sh/api/cask/bdash.json",
    "https://formulae.brew.sh/api/cask/bezel.json",
    "https://formulae.brew.sh/api/cask/blockblock.json",
    "https://formulae.brew.sh/api/cask/browserstacklocal.json",
    "https://formulae.brew.sh/api/cask/cacher.json",
    "https://formulae.brew.sh/api/cask/camunda-modeler.json",
    "https://formulae.brew.sh/api/cask/captin.json",
    "https://formulae.brew.sh/api/cask/cardhop.json",
    "https://formulae.brew.sh/api/cask/cellprofiler.json",
    "https://formulae.brew.sh/api/cask/chime.json",
    "https://formulae.brew.sh/api/cask/chipmunk.json",
    "https://formulae.brew.sh/api/cask/clocker.json",
    "https://formulae.brew.sh/api/cask/clockify.json",
    "https://formulae.brew.sh/api/cask/comfyui.json",
    "https://formulae.brew.sh/api/cask/cork.json",
    "https://formulae.brew.sh/api/cask/customshortcuts.json",
    "https://formulae.brew.sh/api/cask/debookee.json",
    "https://formulae.brew.sh/api/cask/devonsphere-express.json",
    "https://formulae.brew.sh/api/cask/dialpad.json",
    "https://formulae.brew.sh/api/cask/dictionaries.json",
    "https://formulae.brew.sh/api/cask/droplr.json",
    "https://formulae.brew.sh/api/cask/dupeguru.json",
    "https://formulae.brew.sh/api/cask/etrecheckpro.json",
    "https://formulae.brew.sh/api/cask/farrago.json",
    "https://formulae.brew.sh/api/cask/fastmail.json",
    "https://formulae.brew.sh/api/cask/file-juicer.json",
    "https://formulae.brew.sh/api/cask/freefilesync.json",
    "https://formulae.brew.sh/api/cask/gitfox.json",
    "https://formulae.brew.sh/api/cask/gitify.json",
    "https://formulae.brew.sh/api/cask/gpodder.json",
    "https://formulae.brew.sh/api/cask/graphicconverter.json",
    "https://formulae.brew.sh/api/cask/grids.json",
    "https://formulae.brew.sh/api/cask/helium.json",
    "https://formulae.brew.sh/api/cask/hidock.json",
    "https://formulae.brew.sh/api/cask/hot.json",
    "https://formulae.brew.sh/api/cask/houdahspot.json",
    "https://formulae.brew.sh/api/cask/imagej.json",
    "https://formulae.brew.sh/api/cask/iris.json",
    "https://formulae.brew.sh/api/cask/istat-menus.json",
    "https://formulae.brew.sh/api/cask/keepingyouawake.json",
    "https://formulae.brew.sh/api/cask/keyboardcleantool.json",
    "https://formulae.brew.sh/api/cask/latest.json",
    "https://formulae.brew.sh/api/cask/launchcontrol.json",
    "https://formulae.brew.sh/api/cask/lifesize.json",
    "https://formulae.brew.sh/api/cask/lingon-x.json",
    "https://formulae.brew.sh/api/cask/locationsimulator.json",
    "https://formulae.brew.sh/api/cask/lunasea.json",
    "https://formulae.brew.sh/api/cask/macjournal.json",
    "https://formulae.brew.sh/api/cask/macpacker.json",
    "https://formulae.brew.sh/api/cask/macsyzones.json",
    "https://formulae.brew.sh/api/cask/mactracker.json",
    "https://formulae.brew.sh/api/cask/melodics.json",
    "https://formulae.brew.sh/api/cask/memory.json",
    "https://formulae.brew.sh/api/cask/merlin-project.json",
    "https://formulae.brew.sh/api/cask/minisim.json",
    "https://formulae.brew.sh/api/cask/minstaller.json",
    "https://formulae.brew.sh/api/cask/mission-control-plus.json",
    "https://formulae.brew.sh/api/cask/murus.json",
    "https://formulae.brew.sh/api/cask/mx-power-gadget.json",
    "https://formulae.brew.sh/api/cask/namechanger.json",
    "https://formulae.brew.sh/api/cask/native-access.json",
    "https://formulae.brew.sh/api/cask/netron.json",
    "https://formulae.brew.sh/api/cask/nocturnal.json",
    "https://formulae.brew.sh/api/cask/notchnook.json",
    "https://formulae.brew.sh/api/cask/ok-json.json",
    "https://formulae.brew.sh/api/cask/onlyoffice.json",
    "https://formulae.brew.sh/api/cask/openrct2.json",
    "https://formulae.brew.sh/api/cask/phoenix.json",
    "https://formulae.brew.sh/api/cask/photostickies.json",
    "https://formulae.brew.sh/api/cask/pibar.json",
    "https://formulae.brew.sh/api/cask/piezo.json",
    "https://formulae.brew.sh/api/cask/pingplotter.json",
    "https://formulae.brew.sh/api/cask/plex-htpc.json",
    "https://formulae.brew.sh/api/cask/plex-media-server.json",
    "https://formulae.brew.sh/api/cask/positron.json",
    "https://formulae.brew.sh/api/cask/powerphotos.json",
    "https://formulae.brew.sh/api/cask/pritunl.json",
    "https://formulae.brew.sh/api/cask/private-internet-access.json",
    "https://formulae.brew.sh/api/cask/prizmo.json",
    "https://formulae.brew.sh/api/cask/qlmarkdown.json",
    "https://formulae.brew.sh/api/cask/rapidapi.json",
    "https://formulae.brew.sh/api/cask/rapidweaver.json",
    "https://formulae.brew.sh/api/cask/rawtherapee.json",
    "https://formulae.brew.sh/api/cask/reminders-menubar.json",
    "https://formulae.brew.sh/api/cask/remote-buddy.json",
    "https://formulae.brew.sh/api/cask/retrobatch.json",
    "https://formulae.brew.sh/api/cask/rewritebar.json",
    "https://formulae.brew.sh/api/cask/screen-studio.json",
    "https://formulae.brew.sh/api/cask/screenflick.json",
    "https://formulae.brew.sh/api/cask/secretive.json",
    "https://formulae.brew.sh/api/cask/selfcontrol.json",
    "https://formulae.brew.sh/api/cask/sentinel.json",
    "https://formulae.brew.sh/api/cask/setapp.json",
    "https://formulae.brew.sh/api/cask/shifty.json",
    "https://formulae.brew.sh/api/cask/sidenotes.json",
    "https://formulae.brew.sh/api/cask/simple-comic.json",
    "https://formulae.brew.sh/api/cask/simpledemviewer.json",
    "https://formulae.brew.sh/api/cask/sirimote.json",
    "https://formulae.brew.sh/api/cask/slidepad.json",
    "https://formulae.brew.sh/api/cask/sloth.json",
    "https://formulae.brew.sh/api/cask/smoothscroll.json",
    "https://formulae.brew.sh/api/cask/smultron.json",
    "https://formulae.brew.sh/api/cask/soulver.json",
    "https://formulae.brew.sh/api/cask/sparkle.json",
    "https://formulae.brew.sh/api/cask/squash.json",
    "https://formulae.brew.sh/api/cask/standard-notes.json",
    "https://formulae.brew.sh/api/cask/stellarium.json",
    "https://formulae.brew.sh/api/cask/stillcolor.json",
    "https://formulae.brew.sh/api/cask/subethaedit.json",
    "https://formulae.brew.sh/api/cask/sunsama.json",
    "https://formulae.brew.sh/api/cask/surge.json",
    "https://formulae.brew.sh/api/cask/swift-quit.json",
    "https://formulae.brew.sh/api/cask/swiftbar.json",
    "https://formulae.brew.sh/api/cask/switch.json",
    "https://formulae.brew.sh/api/cask/syncmate.json",
    "https://formulae.brew.sh/api/cask/syntax-highlight.json",
    "https://formulae.brew.sh/api/cask/systhist.json",
    "https://formulae.brew.sh/api/cask/tabula.json",
    "https://formulae.brew.sh/api/cask/taccy.json",
    "https://formulae.brew.sh/api/cask/texshop.json",
    "https://formulae.brew.sh/api/cask/thumbsup.json",
    "https://formulae.brew.sh/api/cask/timer.json",
    "https://formulae.brew.sh/api/cask/timescribe.json",
    "https://formulae.brew.sh/api/cask/tomatobar.json",
    "https://formulae.brew.sh/api/cask/trex.json",
    "https://formulae.brew.sh/api/cask/tuple.json",
    "https://formulae.brew.sh/api/cask/unicodechecker.json",
    "https://formulae.brew.sh/api/cask/vellum.json",
    "https://formulae.brew.sh/api/cask/versions.json",
    "https://formulae.brew.sh/api/cask/vnote.json",
    "https://formulae.brew.sh/api/cask/vpn-tracker-365.json",
    "https://formulae.brew.sh/api/cask/vysor.json",
    "https://formulae.brew.sh/api/cask/wavebox.json",
    "https://formulae.brew.sh/api/cask/whatroute.json",
    "https://formulae.brew.sh/api/cask/whisky.json",
    "https://formulae.brew.sh/api/cask/wins.json",
    "https://formulae.brew.sh/api/cask/wordservice.json",
    "https://formulae.brew.sh/api/cask/xattred.json",
    "https://formulae.brew.sh/api/cask/xmenu.json",
    "https://formulae.brew.sh/api/cask/yippy.json",
    "https://formulae.brew.sh/api/cask/zight.json",
    "https://formulae.brew.sh/api/cask/linear-linear.json",
    "https://formulae.brew.sh/api/cask/notion-mail.json",
    "https://formulae.brew.sh/api/cask/codex.json",
]

# DMG
homebrew_cask_urls = [
    "https://formulae.brew.sh/api/cask/mysqlworkbench.json",
    "https://formulae.brew.sh/api/cask/multiapp.json",
    "https://formulae.brew.sh/api/cask/recut.json",
    "https://formulae.brew.sh/api/cask/firefox@esr.json",
    "https://formulae.brew.sh/api/cask/firefox@developer-edition.json",
    "https://formulae.brew.sh/api/cask/lunatask.json",
    "https://formulae.brew.sh/api/cask/threema.json",
    "https://formulae.brew.sh/api/cask/advanced-renamer.json",
    "https://formulae.brew.sh/api/cask/phoenix-slides.json",
    "https://formulae.brew.sh/api/cask/maestral.json",
    "https://formulae.brew.sh/api/cask/mindjet-mindmanager.json",
    "https://formulae.brew.sh/api/cask/retcon.json",
    "https://formulae.brew.sh/api/cask/sketchup.json",
    "https://formulae.brew.sh/api/cask/gephi.json",
    "https://formulae.brew.sh/api/cask/magicquit.json",
    "https://formulae.brew.sh/api/cask/xca.json",
    "https://formulae.brew.sh/api/cask/fathom.json",
    "https://formulae.brew.sh/api/cask/vimcal.json",
    "https://formulae.brew.sh/api/cask/studio-3t.json",
    "https://formulae.brew.sh/api/cask/proton-pass.json",
    "https://formulae.brew.sh/api/cask/bome-network.json",
    "https://formulae.brew.sh/api/cask/antinote.json",
    "https://formulae.brew.sh/api/cask/reqable.json",
    "https://formulae.brew.sh/api/cask/steermouse.json",
    "https://formulae.brew.sh/api/cask/pixelsnap.json",
    "https://formulae.brew.sh/api/cask/processspy.json",
    "https://formulae.brew.sh/api/cask/highlight.json",
    "https://formulae.brew.sh/api/cask/updf.json",
    "https://formulae.brew.sh/api/cask/binary-ninja-free.json",
    "https://formulae.brew.sh/api/cask/rive.json",
    "https://formulae.brew.sh/api/cask/paletro.json",
    "https://formulae.brew.sh/api/cask/dangerzone.json",
    "https://formulae.brew.sh/api/cask/bitwig-studio.json",
    "https://formulae.brew.sh/api/cask/aircall.json",
    "https://formulae.brew.sh/api/cask/nosql-workbench.json",
    "https://formulae.brew.sh/api/cask/rocket-typist.json",
    "https://formulae.brew.sh/api/cask/clop.json",
    "https://formulae.brew.sh/api/cask/hyperkey.json",
    "https://formulae.brew.sh/api/cask/wondershare-filmora.json",
    "https://formulae.brew.sh/api/cask/xnapper.json",
    "https://formulae.brew.sh/api/cask/syncovery.json",
    "https://formulae.brew.sh/api/cask/markedit.json",
    "https://formulae.brew.sh/api/cask/dockside.json",
    "https://formulae.brew.sh/api/cask/wave.json",
    "https://formulae.brew.sh/api/cask/ente-auth.json",
    "https://formulae.brew.sh/api/cask/ente.json",
    "https://formulae.brew.sh/api/cask/istherenet.json",
    "https://formulae.brew.sh/api/cask/name-mangler.json",
    "https://formulae.brew.sh/api/cask/witch.json",
    "https://formulae.brew.sh/api/cask/readest.json",
    "https://formulae.brew.sh/api/cask/middle.json",
    "https://formulae.brew.sh/api/cask/transnomino.json",
    "https://formulae.brew.sh/api/cask/noun-project.json",
    "https://formulae.brew.sh/api/cask/piphero.json",
    "https://formulae.brew.sh/api/cask/tofu.json",
    "https://formulae.brew.sh/api/cask/wondershare-edrawmax.json",
    "https://formulae.brew.sh/api/cask/tabtab.json",
    "https://formulae.brew.sh/api/cask/sabnzbd.json",
    "https://formulae.brew.sh/api/cask/archaeology.json",
    "https://formulae.brew.sh/api/cask/jamie.json",
    "https://formulae.brew.sh/api/cask/a-better-finder-rename.json",
    "https://formulae.brew.sh/api/cask/acronis-true-image.json",
    "https://formulae.brew.sh/api/cask/airbuddy.json",
    "https://formulae.brew.sh/api/cask/airparrot.json",
    "https://formulae.brew.sh/api/cask/mural.json",
    "https://formulae.brew.sh/api/cask/mixxx.json",
    "https://formulae.brew.sh/api/cask/mobirise.json",
    "https://formulae.brew.sh/api/cask/thunderbird.json",
    "https://formulae.brew.sh/api/cask/multiviewer-for-f1.json",
    "https://formulae.brew.sh/api/cask/nitro-pdf-pro.json",
    "https://formulae.brew.sh/api/cask/nordpass.json",
    "https://formulae.brew.sh/api/cask/novabench.json",
    "https://formulae.brew.sh/api/cask/omnifocus.json",
    "https://formulae.brew.sh/api/cask/omnioutliner.json",
    "https://formulae.brew.sh/api/cask/pdf-pals.json",
    "https://formulae.brew.sh/api/cask/orka-desktop.json",
    "https://formulae.brew.sh/api/cask/packages.json",
    "https://formulae.brew.sh/api/cask/popchar.json",
    "https://formulae.brew.sh/api/cask/postico.json",
    "https://formulae.brew.sh/api/cask/portx.json",
    "https://formulae.brew.sh/api/cask/pulsar.json",
    "https://formulae.brew.sh/api/cask/qspace-pro.json",
    "https://formulae.brew.sh/api/cask/raindropio.json",
    "https://formulae.brew.sh/api/cask/reflector.json",
    "https://formulae.brew.sh/api/cask/rectangle-pro.json",
    "https://formulae.brew.sh/api/cask/rocket-chat.json",
    "https://formulae.brew.sh/api/cask/rocket.json",
    "https://formulae.brew.sh/api/cask/rsyncui.json",
    "https://formulae.brew.sh/api/cask/pika.json",
    "https://formulae.brew.sh/api/cask/requestly.json",
    "https://formulae.brew.sh/api/cask/adguard.json",
    "https://formulae.brew.sh/api/cask/orcaslicer.json",
    "https://formulae.brew.sh/api/cask/lookaway.json",
    "https://formulae.brew.sh/api/cask/kap.json",
    "https://formulae.brew.sh/api/cask/bambu-studio.json",
    "https://formulae.brew.sh/api/cask/upscayl.json",
    "https://formulae.brew.sh/api/cask/apifox.json",
    "https://formulae.brew.sh/api/cask/nvidia-geforce-now.json",
    "https://formulae.brew.sh/api/cask/rectangle.json",
    "https://formulae.brew.sh/api/cask/dosbox.json",
    "https://formulae.brew.sh/api/cask/qview.json",
    "https://formulae.brew.sh/api/cask/rider.json",
    "https://formulae.brew.sh/api/cask/stretchly.json",
    "https://formulae.brew.sh/api/cask/proton-mail.json",
    "https://formulae.brew.sh/api/cask/proton-drive.json",
    "https://formulae.brew.sh/api/cask/cryptomator.json",
    "https://formulae.brew.sh/api/cask/veracrypt.json",
    "https://formulae.brew.sh/api/cask/dockdoor.json",
    "https://formulae.brew.sh/api/cask/yaak.json",
    "https://formulae.brew.sh/api/cask/messenger.json",
    "https://formulae.brew.sh/api/cask/meetingbar.json",
    "https://formulae.brew.sh/api/cask/zap.json",
    "https://formulae.brew.sh/api/cask/qq.json",
    "https://formulae.brew.sh/api/cask/mouseless.json",
    "https://formulae.brew.sh/api/cask/arduino-ide.json",
    "https://formulae.brew.sh/api/cask/visualvm.json",
    "https://formulae.brew.sh/api/cask/grandperspective.json",
    "https://formulae.brew.sh/api/cask/moonlight.json",
    "https://formulae.brew.sh/api/cask/freetube.json",
    "https://formulae.brew.sh/api/cask/chatwise.json",
    "https://formulae.brew.sh/api/cask/motrix.json",
    "https://formulae.brew.sh/api/cask/phpstorm.json",
    "https://formulae.brew.sh/api/cask/qlvideo.json",
    "https://formulae.brew.sh/api/cask/marta.json",
    "https://formulae.brew.sh/api/cask/mockoon.json",
    "https://formulae.brew.sh/api/cask/proxyman.json",
    "https://formulae.brew.sh/api/cask/typora.json",
    "https://formulae.brew.sh/api/cask/meld.json",
    "https://formulae.brew.sh/api/cask/freelens.json",
    "https://formulae.brew.sh/api/cask/teamviewer-host.json",
    "https://formulae.brew.sh/api/cask/teamviewer-quicksupport.json",
    "https://formulae.brew.sh/api/cask/skim.json",
    "https://formulae.brew.sh/api/cask/lens.json",
    "https://formulae.brew.sh/api/cask/coteditor.json",
    "https://formulae.brew.sh/api/cask/trae.json",
    "https://formulae.brew.sh/api/cask/tigervnc-viewer.json",
    "https://formulae.brew.sh/api/cask/tunnelblick.json",
    "https://formulae.brew.sh/api/cask/wechat.json",
    "https://formulae.brew.sh/api/cask/redis-insight.json",
    "https://formulae.brew.sh/api/cask/mos.json",
    "https://formulae.brew.sh/api/cask/localsend.json",
    "https://formulae.brew.sh/api/cask/qbittorrent.json",
    "https://formulae.brew.sh/api/cask/monitorcontrol.json",
    "https://formulae.brew.sh/api/cask/lulu.json",
    "https://formulae.brew.sh/api/cask/headlamp.json",
    "https://formulae.brew.sh/api/cask/librewolf.json",
    "https://formulae.brew.sh/api/cask/dbeaver-community.json",
    "https://formulae.brew.sh/api/cask/rustdesk.json",
    "https://formulae.brew.sh/api/cask/easydict.json",
    "https://formulae.brew.sh/api/cask/unnaturalscrollwheels.json",
    "https://formulae.brew.sh/api/cask/downie.json",
    "https://formulae.brew.sh/api/cask/hazel.json",
    "https://formulae.brew.sh/api/cask/cleanshot.json",
    "https://formulae.brew.sh/api/cask/pastebot.json",
    "https://formulae.brew.sh/api/cask/omnissa-horizon-client.json",
    "https://formulae.brew.sh/api/cask/adobe-creative-cloud.json",
    "https://formulae.brew.sh/api/cask/google-chrome.json",
    "https://formulae.brew.sh/api/cask/zoom.json",
    "https://formulae.brew.sh/api/cask/firefox.json",
    "https://formulae.brew.sh/api/cask/slack.json",
    "https://formulae.brew.sh/api/cask/microsoft-teams.json",
    "https://formulae.brew.sh/api/cask/spotify.json",
    "https://formulae.brew.sh/api/cask/intune-company-portal.json",
    "https://formulae.brew.sh/api/cask/windows-app.json",
    "https://formulae.brew.sh/api/cask/parallels.json",
    "https://formulae.brew.sh/api/cask/keepassxc.json",
    "https://formulae.brew.sh/api/cask/synology-drive.json",
    "https://formulae.brew.sh/api/cask/grammarly-desktop.json",
    "https://formulae.brew.sh/api/cask/todoist.json",
    "https://formulae.brew.sh/api/cask/xmind.json",
    "https://formulae.brew.sh/api/cask/docker.json",
    "https://formulae.brew.sh/api/cask/vlc.json",
    "https://formulae.brew.sh/api/cask/bitwarden.json",
    "https://formulae.brew.sh/api/cask/miro.json",
    "https://formulae.brew.sh/api/cask/snagit.json",
    "https://formulae.brew.sh/api/cask/canva.json",
    "https://formulae.brew.sh/api/cask/blender.json",
    "https://formulae.brew.sh/api/cask/webex.json",
    "https://formulae.brew.sh/api/cask/mongodb-compass.json",
    "https://formulae.brew.sh/api/cask/suspicious-package.json",
    "https://formulae.brew.sh/api/cask/notion.json",
    "https://formulae.brew.sh/api/cask/anydesk.json",
    "https://formulae.brew.sh/api/cask/android-studio.json",
    "https://formulae.brew.sh/api/cask/brave-browser.json",
    "https://formulae.brew.sh/api/cask/evernote.json",
    "https://formulae.brew.sh/api/cask/dropbox.json",
    "https://formulae.brew.sh/api/cask/krisp.json",
    "https://formulae.brew.sh/api/cask/obsidian.json",
    "https://formulae.brew.sh/api/cask/rstudio.json",
    "https://formulae.brew.sh/api/cask/utm.json",
    "https://formulae.brew.sh/api/cask/vnc-viewer.json",
    "https://formulae.brew.sh/api/cask/powershell.json",
    "https://formulae.brew.sh/api/cask/betterdisplay.json",
    "https://formulae.brew.sh/api/cask/orbstack.json",
    "https://formulae.brew.sh/api/cask/capcut.json",
    "https://formulae.brew.sh/api/cask/bbedit.json",
    "https://formulae.brew.sh/api/cask/termius.json",
    "https://formulae.brew.sh/api/cask/corretto@21.json",
    "https://formulae.brew.sh/api/cask/anki.json",
    "https://formulae.brew.sh/api/cask/netbeans.json",
    "https://formulae.brew.sh/api/cask/audacity.json",
    "https://formulae.brew.sh/api/cask/chatgpt.json",
    "https://formulae.brew.sh/api/cask/citrix-workspace.json",
    "https://formulae.brew.sh/api/cask/datagrip.json",
    "https://formulae.brew.sh/api/cask/discord.json",
    "https://formulae.brew.sh/api/cask/duckduckgo.json",
    "https://formulae.brew.sh/api/cask/elgato-wave-link.json",
    "https://formulae.brew.sh/api/cask/elgato-camera-hub.json",
    "https://formulae.brew.sh/api/cask/elgato-stream-deck.json",
    "https://formulae.brew.sh/api/cask/drawio.json",
    "https://formulae.brew.sh/api/cask/foxit-pdf-editor.json",
    "https://formulae.brew.sh/api/cask/gimp.json",
    "https://formulae.brew.sh/api/cask/geany.json",
    "https://formulae.brew.sh/api/cask/goland.json",
    "https://formulae.brew.sh/api/cask/google-drive.json",
    "https://formulae.brew.sh/api/cask/santa.json",
    "https://formulae.brew.sh/api/cask/intellij-idea-ce.json",
    "https://formulae.brew.sh/api/cask/keeper-password-manager.json",
    "https://formulae.brew.sh/api/cask/libreoffice.json",
    "https://formulae.brew.sh/api/cask/podman-desktop.json",
    "https://formulae.brew.sh/api/cask/pycharm-ce.json",
    "https://formulae.brew.sh/api/cask/splashtop-business.json",
    "https://formulae.brew.sh/api/cask/tailscale.json",
    "https://formulae.brew.sh/api/cask/webstorm.json",
    "https://formulae.brew.sh/api/cask/wireshark.json",
    "https://formulae.brew.sh/api/cask/yubico-yubikey-manager.json",
    "https://formulae.brew.sh/api/cask/imazing.json",
    "https://formulae.brew.sh/api/cask/imazing-profile-editor.json",
    "https://formulae.brew.sh/api/cask/ghostty.json",
    "https://formulae.brew.sh/api/cask/git-credential-manager.json",
    "https://formulae.brew.sh/api/cask/macfuse.json",
    "https://formulae.brew.sh/api/cask/raycast.json",
    "https://formulae.brew.sh/api/cask/zulu.json",
    "https://formulae.brew.sh/api/cask/stats.json",
    "https://formulae.brew.sh/api/cask/temurin.json",
    "https://formulae.brew.sh/api/cask/bruno.json",
    "https://formulae.brew.sh/api/cask/zed.json",
    "https://formulae.brew.sh/api/cask/virtualbox.json",
    "https://formulae.brew.sh/api/cask/kitty.json",
    "https://formulae.brew.sh/api/cask/db-browser-for-sqlite.json",
    "https://formulae.brew.sh/api/cask/alacritty.json",
    "https://formulae.brew.sh/api/cask/pgadmin4.json",
    "https://formulae.brew.sh/api/cask/iina.json",
    "https://formulae.brew.sh/api/cask/karabiner-elements.json",
    "https://formulae.brew.sh/api/cask/mactex.json",
    "https://formulae.brew.sh/api/cask/microsoft-edge.json",
    "https://formulae.brew.sh/api/cask/calibre.json",
    "https://formulae.brew.sh/api/cask/obs.json",
    "https://formulae.brew.sh/api/cask/keka.json",
    "https://formulae.brew.sh/api/cask/balenaetcher.json",
    "https://formulae.brew.sh/api/cask/rancher.json",
    "https://formulae.brew.sh/api/cask/vscodium.json",
    "https://formulae.brew.sh/api/cask/mounty.json",
    "https://formulae.brew.sh/api/cask/microsoft-office.json",
    "https://formulae.brew.sh/api/cask/transmission.json",
    "https://formulae.brew.sh/api/cask/shottr.json",
    "https://formulae.brew.sh/api/cask/clipy.json",
    "https://formulae.brew.sh/api/cask/windsurf.json",
    "https://formulae.brew.sh/api/cask/freecad.json",
    "https://formulae.brew.sh/api/cask/insomnia.json",
    "https://formulae.brew.sh/api/cask/flameshot.json",
    "https://formulae.brew.sh/api/cask/onedrive.json",
    "https://formulae.brew.sh/api/cask/lm-studio.json",
    "https://formulae.brew.sh/api/cask/privileges.json",
    "https://formulae.brew.sh/api/cask/zen-browser.json",
    "https://formulae.brew.sh/api/cask/sync.json",
    "https://formulae.brew.sh/api/cask/opera.json",
    "https://formulae.brew.sh/api/cask/protonvpn.json",
    "https://formulae.brew.sh/api/cask/little-snitch.json",
    "https://formulae.brew.sh/api/cask/micro-snitch.json",
    "https://formulae.brew.sh/api/cask/jetbrains-toolbox.json",
    "https://formulae.brew.sh/api/cask/clion.json",
    "https://formulae.brew.sh/api/cask/krita.json",
    "https://formulae.brew.sh/api/cask/onyx.json",
    "https://formulae.brew.sh/api/cask/hiddenbar.json",
    "https://formulae.brew.sh/api/cask/steam.json",
    "https://formulae.brew.sh/api/cask/gifox.json",
    "https://formulae.brew.sh/api/cask/inkscape.json",
    "https://formulae.brew.sh/api/cask/boltai.json",
    "https://formulae.brew.sh/api/cask/boxcryptor.json",
    "https://formulae.brew.sh/api/cask/breaktimer.json",
    "https://formulae.brew.sh/api/cask/anydo.json",
    "https://formulae.brew.sh/api/cask/apidog.json",
    "https://formulae.brew.sh/api/cask/apparency.json",
    "https://formulae.brew.sh/api/cask/badgeify.json",
    "https://formulae.brew.sh/api/cask/airtable.json",
    "https://formulae.brew.sh/api/cask/airy.json",
    "https://formulae.brew.sh/api/cask/amadine.json",
    "https://formulae.brew.sh/api/cask/amazon-chime.json",
    "https://formulae.brew.sh/api/cask/amazon-q.json",
    "https://formulae.brew.sh/api/cask/google-ads-editor.json",
    "https://formulae.brew.sh/api/cask/hazeover.json",
    "https://formulae.brew.sh/api/cask/jellyfin.json",
    "https://formulae.brew.sh/api/cask/gitfinder.json",
    "https://formulae.brew.sh/api/cask/codeedit.json",
    "https://formulae.brew.sh/api/cask/crystalfetch.json",
    "https://formulae.brew.sh/api/cask/dataflare.json",
    "https://formulae.brew.sh/api/cask/dataspell.json",
    "https://formulae.brew.sh/api/cask/dbgate.json",
    "https://formulae.brew.sh/api/cask/devutils.json",
    "https://formulae.brew.sh/api/cask/doughnut.json",
    "https://formulae.brew.sh/api/cask/drawbot.json",
    "https://formulae.brew.sh/api/cask/dropdmg.json",
    "https://formulae.brew.sh/api/cask/elephas.json",
    "https://formulae.brew.sh/api/cask/epic-games.json",
    "https://formulae.brew.sh/api/cask/calmly-writer.json",
    "https://formulae.brew.sh/api/cask/camtasia.json",
    "https://formulae.brew.sh/api/cask/klokki.json",
    "https://formulae.brew.sh/api/cask/langgraph-studio.json",
    "https://formulae.brew.sh/api/cask/joplin.json",
    "https://formulae.brew.sh/api/cask/remote-desktop-manager.json",
    "https://formulae.brew.sh/api/cask/rotato.json",
    "https://formulae.brew.sh/api/cask/tenable-nessus-agent.json",
    "https://formulae.brew.sh/api/cask/8x8-work.json",
    "https://formulae.brew.sh/api/cask/fork.json",
    "https://formulae.brew.sh/api/cask/box-tools.json",
    "https://formulae.brew.sh/api/cask/musescore.json",
    "https://formulae.brew.sh/api/cask/intellij-idea.json",
    "https://formulae.brew.sh/api/cask/handbrake-app.json",
    "https://formulae.brew.sh/api/cask/minecraft.json",
    "https://formulae.brew.sh/api/cask/deepl.json",
    "https://formulae.brew.sh/api/cask/warp.json",
    # New DMG apps (batch 1 - 57 apps)
    "https://formulae.brew.sh/api/cask/aldente.json",
    "https://formulae.brew.sh/api/cask/another-redis-desktop-manager.json",
    "https://formulae.brew.sh/api/cask/appflowy.json",
    "https://formulae.brew.sh/api/cask/audirvana.json",
    "https://formulae.brew.sh/api/cask/avidemux.json",
    "https://formulae.brew.sh/api/cask/backblaze.json",
    "https://formulae.brew.sh/api/cask/beekeeper-studio.json",
    "https://formulae.brew.sh/api/cask/charles.json",
    "https://formulae.brew.sh/api/cask/cheatsheet.json",
    "https://formulae.brew.sh/api/cask/contexts.json",
    "https://formulae.brew.sh/api/cask/craft.json",
    "https://formulae.brew.sh/api/cask/curio.json",
    "https://formulae.brew.sh/api/cask/disk-drill.json",
    "https://formulae.brew.sh/api/cask/elmedia-player.json",
    "https://formulae.brew.sh/api/cask/expandrive.json",
    "https://formulae.brew.sh/api/cask/filen.json",
    "https://formulae.brew.sh/api/cask/floorp.json",
    "https://formulae.brew.sh/api/cask/guilded.json",
    "https://formulae.brew.sh/api/cask/hoppscotch.json",
    "https://formulae.brew.sh/api/cask/http-toolkit.json",
    "https://formulae.brew.sh/api/cask/hype.json",
    "https://formulae.brew.sh/api/cask/jitsi-meet.json",
    "https://formulae.brew.sh/api/cask/kodi.json",
    "https://formulae.brew.sh/api/cask/lapce.json",
    "https://formulae.brew.sh/api/cask/lark.json",
    "https://formulae.brew.sh/api/cask/launchbar.json",
    "https://formulae.brew.sh/api/cask/logseq.json",
    "https://formulae.brew.sh/api/cask/losslesscut.json",
    "https://formulae.brew.sh/api/cask/lunacy.json",
    "https://formulae.brew.sh/api/cask/makemkv.json",
    "https://formulae.brew.sh/api/cask/milanote.json",
    "https://formulae.brew.sh/api/cask/mimestream.json",
    "https://formulae.brew.sh/api/cask/movist-pro.json",
    "https://formulae.brew.sh/api/cask/mullvad-browser.json",
    "https://formulae.brew.sh/api/cask/one-switch.json",
    "https://formulae.brew.sh/api/cask/path-finder.json",
    "https://formulae.brew.sh/api/cask/permute.json",
    "https://formulae.brew.sh/api/cask/plexamp.json",
    "https://formulae.brew.sh/api/cask/resilio-sync.json",
    "https://formulae.brew.sh/api/cask/responsively.json",
    "https://formulae.brew.sh/api/cask/screenflow.json",
    "https://formulae.brew.sh/api/cask/sensei.json",
    "https://formulae.brew.sh/api/cask/sigmaos.json",
    "https://formulae.brew.sh/api/cask/simplenote.json",
    "https://formulae.brew.sh/api/cask/skype.json",
    "https://formulae.brew.sh/api/cask/stremio.json",
    "https://formulae.brew.sh/api/cask/superduper.json",
    "https://formulae.brew.sh/api/cask/surfshark.json",
    "https://formulae.brew.sh/api/cask/tableplus.json",
    "https://formulae.brew.sh/api/cask/topnotch.json",
    "https://formulae.brew.sh/api/cask/tor-browser.json",
    "https://formulae.brew.sh/api/cask/tresorit.json",
    "https://formulae.brew.sh/api/cask/typinator.json",
    "https://formulae.brew.sh/api/cask/viscosity.json",
    "https://formulae.brew.sh/api/cask/vox.json",
    "https://formulae.brew.sh/api/cask/zettlr.json",
    "https://formulae.brew.sh/api/cask/zulip.json",
    # New DMG apps (batch 2 - 65 apps)
    "https://formulae.brew.sh/api/cask/amazon-music.json",
    "https://formulae.brew.sh/api/cask/atext.json",
    "https://formulae.brew.sh/api/cask/birdfont.json",
    "https://formulae.brew.sh/api/cask/biscuit.json",
    "https://formulae.brew.sh/api/cask/bluefish.json",
    "https://formulae.brew.sh/api/cask/brackets.json",
    "https://formulae.brew.sh/api/cask/bunch.json",
    "https://formulae.brew.sh/api/cask/butler.json",
    "https://formulae.brew.sh/api/cask/capacities.json",
    "https://formulae.brew.sh/api/cask/clickup.json",
    "https://formulae.brew.sh/api/cask/commander-one.json",
    "https://formulae.brew.sh/api/cask/cool-retro-term.json",
    "https://formulae.brew.sh/api/cask/copyq.json",
    "https://formulae.brew.sh/api/cask/deezer.json",
    "https://formulae.brew.sh/api/cask/disk-inventory-x.json",
    "https://formulae.brew.sh/api/cask/ditto.json",
    "https://formulae.brew.sh/api/cask/double-commander.json",
    "https://formulae.brew.sh/api/cask/eclipse-ide.json",
    "https://formulae.brew.sh/api/cask/eclipse-java.json",
    "https://formulae.brew.sh/api/cask/extraterm.json",
    "https://formulae.brew.sh/api/cask/ferdium.json",
    "https://formulae.brew.sh/api/cask/fig.json",
    "https://formulae.brew.sh/api/cask/firecamp.json",
    "https://formulae.brew.sh/api/cask/fleet.json",
    "https://formulae.brew.sh/api/cask/fontbase.json",
    "https://formulae.brew.sh/api/cask/fontlab.json",
    "https://formulae.brew.sh/api/cask/franz.json",
    "https://formulae.brew.sh/api/cask/ghost-browser.json",
    "https://formulae.brew.sh/api/cask/go2shell.json",
    "https://formulae.brew.sh/api/cask/graphql-playground.json",
    "https://formulae.brew.sh/api/cask/linearmouse.json",
    "https://formulae.brew.sh/api/cask/marginnote.json",
    "https://formulae.brew.sh/api/cask/mem.json",
    "https://formulae.brew.sh/api/cask/missive.json",
    "https://formulae.brew.sh/api/cask/mucommander.json",
    "https://formulae.brew.sh/api/cask/notion-enhanced.json",
    "https://formulae.brew.sh/api/cask/ocenaudio.json",
    "https://formulae.brew.sh/api/cask/omnidisksweeper.json",
    "https://formulae.brew.sh/api/cask/opera-gx.json",
    "https://formulae.brew.sh/api/cask/polymail.json",
    "https://formulae.brew.sh/api/cask/postbox.json",
    "https://formulae.brew.sh/api/cask/protopie.json",
    "https://formulae.brew.sh/api/cask/pycharm.json",
    "https://formulae.brew.sh/api/cask/qobuz.json",
    "https://formulae.brew.sh/api/cask/quicksilver.json",
    "https://formulae.brew.sh/api/cask/reaper.json",
    "https://formulae.brew.sh/api/cask/roam-research.json",
    "https://formulae.brew.sh/api/cask/roon.json",
    "https://formulae.brew.sh/api/cask/rubymine.json",
    "https://formulae.brew.sh/api/cask/shift.json",
    "https://formulae.brew.sh/api/cask/soapui.json",
    "https://formulae.brew.sh/api/cask/sonos.json",
    "https://formulae.brew.sh/api/cask/stoplight-studio.json",
    "https://formulae.brew.sh/api/cask/streamlabs.json",
    "https://formulae.brew.sh/api/cask/superkey.json",
    "https://formulae.brew.sh/api/cask/textexpander.json",
    "https://formulae.brew.sh/api/cask/transcribe.json",
    "https://formulae.brew.sh/api/cask/twitch-studio.json",
    "https://formulae.brew.sh/api/cask/typeface.json",
    "https://formulae.brew.sh/api/cask/ungoogled-chromium.json",
    "https://formulae.brew.sh/api/cask/waterfox.json",
    "https://formulae.brew.sh/api/cask/wirecast.json",
    # New DMG apps (batch 3 - 53 apps)
    "https://formulae.brew.sh/api/cask/ableton-live-lite.json",
    "https://formulae.brew.sh/api/cask/ableton-live-suite.json",
    "https://formulae.brew.sh/api/cask/actual.json",
    "https://formulae.brew.sh/api/cask/adium.json",
    "https://formulae.brew.sh/api/cask/airdroid.json",
    "https://formulae.brew.sh/api/cask/android-file-transfer.json",
    "https://formulae.brew.sh/api/cask/android-ndk.json",
    "https://formulae.brew.sh/api/cask/applite.json",
    "https://formulae.brew.sh/api/cask/balsamiq-wireframes.json",
    "https://formulae.brew.sh/api/cask/bibdesk.json",
    "https://formulae.brew.sh/api/cask/bilibili.json",
    "https://formulae.brew.sh/api/cask/bluebubbles.json",
    "https://formulae.brew.sh/api/cask/bluej.json",
    "https://formulae.brew.sh/api/cask/boost-note.json",
    "https://formulae.brew.sh/api/cask/bria.json",
    "https://formulae.brew.sh/api/cask/caffeine.json",
    "https://formulae.brew.sh/api/cask/cerebro.json",
    "https://formulae.brew.sh/api/cask/chronosync.json",
    "https://formulae.brew.sh/api/cask/cleanmymac-zh.json",
    "https://formulae.brew.sh/api/cask/clipgrab.json",
    "https://formulae.brew.sh/api/cask/cloudcompare.json",
    "https://formulae.brew.sh/api/cask/cloudmounter.json",
    "https://formulae.brew.sh/api/cask/cncnet.json",
    "https://formulae.brew.sh/api/cask/colorwell.json",
    "https://formulae.brew.sh/api/cask/companion.json",
    "https://formulae.brew.sh/api/cask/coolterm.json",
    "https://formulae.brew.sh/api/cask/crypter.json",
    "https://formulae.brew.sh/api/cask/cursr.json",
    "https://formulae.brew.sh/api/cask/datagraph.json",
    "https://formulae.brew.sh/api/cask/deckset.json",
    "https://formulae.brew.sh/api/cask/deepgit.json",
    "https://formulae.brew.sh/api/cask/defold.json",
    "https://formulae.brew.sh/api/cask/dingtalk.json",
    "https://formulae.brew.sh/api/cask/displaperture.json",
    "https://formulae.brew.sh/api/cask/djview.json",
    "https://formulae.brew.sh/api/cask/dockstation.json",
    "https://formulae.brew.sh/api/cask/dorico.json",
    "https://formulae.brew.sh/api/cask/douyin.json",
    "https://formulae.brew.sh/api/cask/duet.json",
    "https://formulae.brew.sh/api/cask/dust3d.json",
    "https://formulae.brew.sh/api/cask/dynalist.json",
    "https://formulae.brew.sh/api/cask/eclipse-cpp.json",
    "https://formulae.brew.sh/api/cask/eclipse-dsl.json",
    "https://formulae.brew.sh/api/cask/eclipse-installer.json",
    "https://formulae.brew.sh/api/cask/eclipse-jee.json",
    "https://formulae.brew.sh/api/cask/eclipse-modeling.json",
    "https://formulae.brew.sh/api/cask/eclipse-php.json",
    "https://formulae.brew.sh/api/cask/eclipse-rcp.json",
    "https://formulae.brew.sh/api/cask/electric-sheep.json",
    "https://formulae.brew.sh/api/cask/electron-cash.json",
    "https://formulae.brew.sh/api/cask/equinox.json",
    "https://formulae.brew.sh/api/cask/eudic.json",
    "https://formulae.brew.sh/api/cask/far2l.json",
    "https://formulae.brew.sh/api/cask/010-editor.json",
    "https://formulae.brew.sh/api/cask/4k-slideshow-maker.json",
    "https://formulae.brew.sh/api/cask/4k-stogram.json",
    "https://formulae.brew.sh/api/cask/4k-video-downloader.json",
    "https://formulae.brew.sh/api/cask/4k-video-to-mp3.json",
    "https://formulae.brew.sh/api/cask/4k-youtube-to-mp3.json",
    "https://formulae.brew.sh/api/cask/abbyy-finereader-pdf.json",
    "https://formulae.brew.sh/api/cask/activitywatch.json",
    "https://formulae.brew.sh/api/cask/adlock.json",
    "https://formulae.brew.sh/api/cask/adobe-digital-editions.json",
    "https://formulae.brew.sh/api/cask/adobe-dng-converter.json",
    "https://formulae.brew.sh/api/cask/airserver.json",
    "https://formulae.brew.sh/api/cask/airtame.json",
    "https://formulae.brew.sh/api/cask/akiflow.json",
    "https://formulae.brew.sh/api/cask/anytype.json",
    "https://formulae.brew.sh/api/cask/app-cleaner.json",
    "https://formulae.brew.sh/api/cask/archi.json",
    "https://formulae.brew.sh/api/cask/avast-secure-browser.json",
    "https://formulae.brew.sh/api/cask/axure-rp.json",
    "https://formulae.brew.sh/api/cask/beaver-notes.json",
    "https://formulae.brew.sh/api/cask/betaflight-configurator.json",
    "https://formulae.brew.sh/api/cask/binance.json",
    "https://formulae.brew.sh/api/cask/bitbox.json",
    "https://formulae.brew.sh/api/cask/bitrix24.json",
    "https://formulae.brew.sh/api/cask/bluewallet.json",
    "https://formulae.brew.sh/api/cask/boom-3d.json",
    "https://formulae.brew.sh/api/cask/buttercup.json",
    "https://formulae.brew.sh/api/cask/buzz.json",
    "https://formulae.brew.sh/api/cask/calhash.json",
    "https://formulae.brew.sh/api/cask/calibrite-profiler.json",
    "https://formulae.brew.sh/api/cask/captain.json",
    "https://formulae.brew.sh/api/cask/capto.json",
    "https://formulae.brew.sh/api/cask/ccleaner.json",
    "https://formulae.brew.sh/api/cask/chalk.json",
    "https://formulae.brew.sh/api/cask/charmstone.json",
    "https://formulae.brew.sh/api/cask/chatwork.json",
    "https://formulae.brew.sh/api/cask/cheetah3d.json",
    "https://formulae.brew.sh/api/cask/cisco-proximity.json",
    "https://formulae.brew.sh/api/cask/cleanclip.json",
    "https://formulae.brew.sh/api/cask/clipbook.json",
    "https://formulae.brew.sh/api/cask/colour-contrast-analyser.json",
    "https://formulae.brew.sh/api/cask/connect-fonts.json",
    "https://formulae.brew.sh/api/cask/connectmenow.json",
    "https://formulae.brew.sh/api/cask/cursorsense.json",
    "https://formulae.brew.sh/api/cask/darkmodebuddy.json",
    "https://formulae.brew.sh/api/cask/darktable.json",
    "https://formulae.brew.sh/api/cask/default-folder-x.json",
    "https://formulae.brew.sh/api/cask/descript.json",
    "https://formulae.brew.sh/api/cask/desktime.json",
    "https://formulae.brew.sh/api/cask/devknife.json",
    "https://formulae.brew.sh/api/cask/diffmerge.json",
    "https://formulae.brew.sh/api/cask/diffusionbee.json",
    "https://formulae.brew.sh/api/cask/digiexam.json",
    "https://formulae.brew.sh/api/cask/dockfix.json",
    "https://formulae.brew.sh/api/cask/eaglefiler.json",
    "https://formulae.brew.sh/api/cask/electronmail.json",
    "https://formulae.brew.sh/api/cask/electrum.json",
    "https://formulae.brew.sh/api/cask/exifcleaner.json",
    "https://formulae.brew.sh/api/cask/exifrenamer.json",
    "https://formulae.brew.sh/api/cask/fellow.json",
    "https://formulae.brew.sh/api/cask/filemaker-pro.json",
    "https://formulae.brew.sh/api/cask/fing.json",
    "https://formulae.brew.sh/api/cask/flexoptix.json",
    "https://formulae.brew.sh/api/cask/folx.json",
    "https://formulae.brew.sh/api/cask/free-download-manager.json",
    "https://formulae.brew.sh/api/cask/funter.json",
    "https://formulae.brew.sh/api/cask/garmin-express.json",
    "https://formulae.brew.sh/api/cask/gdevelop.json",
    "https://formulae.brew.sh/api/cask/github-copilot-for-xcode.json",
    "https://formulae.brew.sh/api/cask/goodsync.json",
    "https://formulae.brew.sh/api/cask/google-earth-pro.json",
    "https://formulae.brew.sh/api/cask/google-web-designer.json",
    "https://formulae.brew.sh/api/cask/granola.json",
    "https://formulae.brew.sh/api/cask/hex-fiend.json",
    "https://formulae.brew.sh/api/cask/hides.json",
    "https://formulae.brew.sh/api/cask/hma-vpn.json",
    "https://formulae.brew.sh/api/cask/icon-composer.json",
    "https://formulae.brew.sh/api/cask/idagio.json",
    "https://formulae.brew.sh/api/cask/iexplorer.json",
    "https://formulae.brew.sh/api/cask/imazing-converter.json",
    "https://formulae.brew.sh/api/cask/imhex.json",
    "https://formulae.brew.sh/api/cask/input-source-pro.json",
    "https://formulae.brew.sh/api/cask/integrity.json",
    "https://formulae.brew.sh/api/cask/intellidock.json",
    "https://formulae.brew.sh/api/cask/invesalius.json",
    "https://formulae.brew.sh/api/cask/jami.json",
    "https://formulae.brew.sh/api/cask/jamovi.json",
    "https://formulae.brew.sh/api/cask/jasp.json",
    "https://formulae.brew.sh/api/cask/jiggler.json",
    "https://formulae.brew.sh/api/cask/kdenlive.json",
    "https://formulae.brew.sh/api/cask/keeweb.json",
    "https://formulae.brew.sh/api/cask/keyboard-cowboy.json",
    "https://formulae.brew.sh/api/cask/keystore-explorer.json",
    "https://formulae.brew.sh/api/cask/kicad.json",
    "https://formulae.brew.sh/api/cask/kobo.json",
    "https://formulae.brew.sh/api/cask/launchos.json",
    "https://formulae.brew.sh/api/cask/librecad.json",
    "https://formulae.brew.sh/api/cask/lightburn.json",
    "https://formulae.brew.sh/api/cask/limitless.json",
    "https://formulae.brew.sh/api/cask/lo-rain.json",
    "https://formulae.brew.sh/api/cask/local.json",
    "https://formulae.brew.sh/api/cask/loom.json",
    "https://formulae.brew.sh/api/cask/loupedeck.json",
    "https://formulae.brew.sh/api/cask/lunar.json",
    "https://formulae.brew.sh/api/cask/lyx.json",
    "https://formulae.brew.sh/api/cask/maccleaner-pro.json",
    "https://formulae.brew.sh/api/cask/macpilot.json",
    "https://formulae.brew.sh/api/cask/masscode.json",
    "https://formulae.brew.sh/api/cask/megasync.json",
    "https://formulae.brew.sh/api/cask/mellel.json",
    "https://formulae.brew.sh/api/cask/memory-cleaner.json",
    "https://formulae.brew.sh/api/cask/mendeley-reference-manager.json",
    "https://formulae.brew.sh/api/cask/menubarx.json",
    "https://formulae.brew.sh/api/cask/mindmac.json",
    "https://formulae.brew.sh/api/cask/modern-csv.json",
    "https://formulae.brew.sh/api/cask/moom.json",
    "https://formulae.brew.sh/api/cask/mqttx.json",
    "https://formulae.brew.sh/api/cask/multi.json",
    "https://formulae.brew.sh/api/cask/multitouch.json",
    "https://formulae.brew.sh/api/cask/museeks.json",
    "https://formulae.brew.sh/api/cask/nagstamon.json",
    "https://formulae.brew.sh/api/cask/neo-network-utility.json",
    "https://formulae.brew.sh/api/cask/netspot.json",
    "https://formulae.brew.sh/api/cask/nextcloud-talk.json",
    "https://formulae.brew.sh/api/cask/nightfall.json",
    "https://formulae.brew.sh/api/cask/notesnook.json",
    "https://formulae.brew.sh/api/cask/numi.json",
    "https://formulae.brew.sh/api/cask/oka-unarchiver.json",
    "https://formulae.brew.sh/api/cask/omnigraffle.json",
    "https://formulae.brew.sh/api/cask/omniplan.json",
    "https://formulae.brew.sh/api/cask/onionshare.json",
    "https://formulae.brew.sh/api/cask/only-switch.json",
    "https://formulae.brew.sh/api/cask/opal-composer.json",
    "https://formulae.brew.sh/api/cask/openaudible.json",
    "https://formulae.brew.sh/api/cask/openboard.json",
    "https://formulae.brew.sh/api/cask/openlens.json",
    "https://formulae.brew.sh/api/cask/openrefine.json",
    "https://formulae.brew.sh/api/cask/openshot-video-editor.json",
    "https://formulae.brew.sh/api/cask/optimus-player.json",
    "https://formulae.brew.sh/api/cask/pacifist.json",
    "https://formulae.brew.sh/api/cask/pale-moon.json",
    "https://formulae.brew.sh/api/cask/pdfsam-basic.json",
    "https://formulae.brew.sh/api/cask/pencil.json",
    "https://formulae.brew.sh/api/cask/picview.json",
    "https://formulae.brew.sh/api/cask/pitch.json",
    "https://formulae.brew.sh/api/cask/popsql.json",
    "https://formulae.brew.sh/api/cask/preform.json",
    "https://formulae.brew.sh/api/cask/prism.json",
    "https://formulae.brew.sh/api/cask/processing.json",
    "https://formulae.brew.sh/api/cask/proton-mail-bridge.json",
    "https://formulae.brew.sh/api/cask/qgis.json",
    "https://formulae.brew.sh/api/cask/raspberry-pi-imager.json",
    "https://formulae.brew.sh/api/cask/recents.json",
    "https://formulae.brew.sh/api/cask/redis-pro.json",
    "https://formulae.brew.sh/api/cask/retroarch.json",
    "https://formulae.brew.sh/api/cask/rewind.json",
    "https://formulae.brew.sh/api/cask/riverside-studio.json",
    "https://formulae.brew.sh/api/cask/rize.json",
    "https://formulae.brew.sh/api/cask/roboform.json",
    "https://formulae.brew.sh/api/cask/royal-tsx.json",
    "https://formulae.brew.sh/api/cask/runjs.json",
    "https://formulae.brew.sh/api/cask/rustrover.json",
    "https://formulae.brew.sh/api/cask/safe-exam-browser.json",
    "https://formulae.brew.sh/api/cask/sanesidebuttons.json",
    "https://formulae.brew.sh/api/cask/sc-menu.json",
    "https://formulae.brew.sh/api/cask/scratch.json",
    "https://formulae.brew.sh/api/cask/screaming-frog-seo-spider.json",
    "https://formulae.brew.sh/api/cask/scribus.json",
    "https://formulae.brew.sh/api/cask/session.json",
    "https://formulae.brew.sh/api/cask/sf-symbols.json",
    "https://formulae.brew.sh/api/cask/shapr3d.json",
    "https://formulae.brew.sh/api/cask/shotcut.json",
    "https://formulae.brew.sh/api/cask/shureplus-motiv.json",
    "https://formulae.brew.sh/api/cask/silhouette-studio.json",
    "https://formulae.brew.sh/api/cask/slab.json",
    "https://formulae.brew.sh/api/cask/smartsheet.json",
    "https://formulae.brew.sh/api/cask/smartsvn.json",
    "https://formulae.brew.sh/api/cask/sococo.json",
    "https://formulae.brew.sh/api/cask/sonic-visualiser.json",
    "https://formulae.brew.sh/api/cask/sonobus.json",
    "https://formulae.brew.sh/api/cask/sound-control.json",
    "https://formulae.brew.sh/api/cask/soundanchor.json",
    "https://formulae.brew.sh/api/cask/spamsieve.json",
    "https://formulae.brew.sh/api/cask/spitfire-audio.json",
    "https://formulae.brew.sh/api/cask/sqlectron.json",
    "https://formulae.brew.sh/api/cask/ssh-config-editor.json",
    "https://formulae.brew.sh/api/cask/staruml.json",
    "https://formulae.brew.sh/api/cask/supercollider.json",
    "https://formulae.brew.sh/api/cask/swifty.json",
    "https://formulae.brew.sh/api/cask/swish.json",
    "https://formulae.brew.sh/api/cask/taskade.json",
    "https://formulae.brew.sh/api/cask/techsmith-capture.json",
    "https://formulae.brew.sh/api/cask/ticktick.json",
    "https://formulae.brew.sh/api/cask/tiles.json",
    "https://formulae.brew.sh/api/cask/timing.json",
    "https://formulae.brew.sh/api/cask/tradingview.json",
    "https://formulae.brew.sh/api/cask/transfer.json",
    "https://formulae.brew.sh/api/cask/trezor-suite.json",
    "https://formulae.brew.sh/api/cask/tribler.json",
    "https://formulae.brew.sh/api/cask/tuta-mail.json",
    "https://formulae.brew.sh/api/cask/ukelele.json",
    "https://formulae.brew.sh/api/cask/ultimaker-cura.json",
    "https://formulae.brew.sh/api/cask/unity-hub.json",
    "https://formulae.brew.sh/api/cask/vanilla.json",
    "https://formulae.brew.sh/api/cask/via.json",
    "https://formulae.brew.sh/api/cask/virtualbuddy.json",
    "https://formulae.brew.sh/api/cask/visual-paradigm.json",
    "https://formulae.brew.sh/api/cask/vuescan.json",
    "https://formulae.brew.sh/api/cask/vyprvpn.json",
    "https://formulae.brew.sh/api/cask/wealthfolio.json",
    "https://formulae.brew.sh/api/cask/webcatalog.json",
    "https://formulae.brew.sh/api/cask/weektodo.json",
    "https://formulae.brew.sh/api/cask/whispering.json",
    "https://formulae.brew.sh/api/cask/xld.json",
    "https://formulae.brew.sh/api/cask/xmplify.json",
    "https://formulae.brew.sh/api/cask/xnconvert.json",
    "https://formulae.brew.sh/api/cask/xnviewmp.json",
    "https://formulae.brew.sh/api/cask/yacreader.json",
    "https://formulae.brew.sh/api/cask/yed.json",
    "https://formulae.brew.sh/api/cask/yubico-authenticator.json",
    "https://formulae.brew.sh/api/cask/zappy.json",
    "https://formulae.brew.sh/api/cask/zotero.json",
    "https://formulae.brew.sh/api/cask/zwift.json",
    "https://formulae.brew.sh/api/cask/egnyte.json",
    "https://formulae.brew.sh/api/cask/claude-code.json",
    "https://formulae.brew.sh/api/cask/chatgpt-atlas.json",
]

# PKG in DMG URLs
pkg_in_dmg_urls = [
    "https://formulae.brew.sh/api/cask/jabra-direct.json",
    "https://formulae.brew.sh/api/cask/rhino.json",
    "https://formulae.brew.sh/api/cask/tableau.json",
    "https://formulae.brew.sh/api/cask/autodesk-fusion.json",
    "https://formulae.brew.sh/api/cask/nomachine.json",
    "https://formulae.brew.sh/api/cask/adobe-acrobat-reader.json",
    "https://formulae.brew.sh/api/cask/adobe-acrobat-pro.json",
    "https://formulae.brew.sh/api/cask/openvpn-connect.json",
    "https://formulae.brew.sh/api/cask/chrome-remote-desktop-host.json",
    "https://formulae.brew.sh/api/cask/crashplan.json",
    "https://formulae.brew.sh/api/cask/appgate-sdp-client.json",
    "https://formulae.brew.sh/api/cask/splashtop-streamer.json",
    # New PKG-in-DMG apps (batch 1 - 1 app)
    "https://formulae.brew.sh/api/cask/gpg-suite.json",
    "https://formulae.brew.sh/api/cask/wacom-tablet.json",
    # Note: tuxera-ntfs removed - has directory-based PKG inside .mpkg that needs special handling
]

# PKG in PKG URLs (some are ZIP files containing PKG that contains inner PKGs)
pkg_in_pkg_urls = [
    "https://formulae.brew.sh/api/cask/insta360-studio.json",
    "https://formulae.brew.sh/api/cask/blurscreen.json",
    "https://formulae.brew.sh/api/cask/topaz-gigapixel-ai.json",
    "https://formulae.brew.sh/api/cask/parallels-client.json",
    "https://formulae.brew.sh/api/cask/okta-advanced-server-access.json",
    "https://formulae.brew.sh/api/cask/wire.json",
    "https://formulae.brew.sh/api/cask/twingate.json",
    "https://formulae.brew.sh/api/cask/aws-vpn-client.json",
    "https://formulae.brew.sh/api/cask/malwarebytes.json",
    "https://formulae.brew.sh/api/cask/nordlayer.json",
    "https://formulae.brew.sh/api/cask/nordlocker.json",
    "https://formulae.brew.sh/api/cask/nudge.json",
    "https://formulae.brew.sh/api/cask/orka.json",
    "https://formulae.brew.sh/api/cask/sony-ps-remote-play.json",
    "https://formulae.brew.sh/api/cask/philips-hue-sync.json",
    "https://formulae.brew.sh/api/cask/nordvpn.json",
    "https://formulae.brew.sh/api/cask/gyazo.json"
]

# PKG
pkg_urls = [
    "https://formulae.brew.sh/api/cask/mist.json",
    "https://formulae.brew.sh/api/cask/gdisk.json",
    "https://formulae.brew.sh/api/cask/parsec.json",
    "https://formulae.brew.sh/api/cask/thonny.json",
    "https://formulae.brew.sh/api/cask/quarto.json",
    "https://formulae.brew.sh/api/cask/squirrel.json",
    "https://formulae.brew.sh/api/cask/displaylink.json",
    "https://formulae.brew.sh/api/cask/background-music.json",
    "https://formulae.brew.sh/api/cask/nextcloud.json",
    "https://formulae.brew.sh/api/cask/cloudflare-warp.json",
    "https://formulae.brew.sh/api/cask/cisco-jabber.json",
    "https://formulae.brew.sh/api/cask/microsoft-auto-update.json",
    "https://formulae.brew.sh/api/cask/box-drive.json",
    "https://formulae.brew.sh/api/cask/session-manager-plugin.json",
    "https://formulae.brew.sh/api/cask/microsoft-office-businesspro.json",
    # New PKG apps (batch 1 - 4 apps)
    "https://formulae.brew.sh/api/cask/arq.json",
    "https://formulae.brew.sh/api/cask/mega.json",
    "https://formulae.brew.sh/api/cask/mullvad-vpn.json",
    "https://formulae.brew.sh/api/cask/multipass.json",
    # New PKG apps (batch 2 - 1 app)
    "https://formulae.brew.sh/api/cask/whatsize.json",
    # New PKG apps (batch 3 - 12 apps)
    "https://formulae.brew.sh/api/cask/aptible.json",
    "https://formulae.brew.sh/api/cask/bankid.json",
    "https://formulae.brew.sh/api/cask/basictex.json",
    "https://formulae.brew.sh/api/cask/blackhole-16ch.json",
    "https://formulae.brew.sh/api/cask/blackhole-2ch.json",
    "https://formulae.brew.sh/api/cask/blackhole-64ch.json",
    "https://formulae.brew.sh/api/cask/clamxav.json",
    "https://formulae.brew.sh/api/cask/displaycal.json",
    "https://formulae.brew.sh/api/cask/duo-connect.json",
    "https://formulae.brew.sh/api/cask/emclient.json",
    "https://formulae.brew.sh/api/cask/enclave.json",
    "https://formulae.brew.sh/api/cask/enpass.json",
    "https://formulae.brew.sh/api/cask/bricklink-studio.json",
    "https://formulae.brew.sh/api/cask/digikam.json",
    "https://formulae.brew.sh/api/cask/dymo-connect.json",
    "https://formulae.brew.sh/api/cask/expressvpn.json",
    "https://formulae.brew.sh/api/cask/fuse-t.json",
    "https://formulae.brew.sh/api/cask/gog-galaxy.json",
    "https://formulae.brew.sh/api/cask/ibm-aspera-connect.json",
    "https://formulae.brew.sh/api/cask/low-profile.json",
    "https://formulae.brew.sh/api/cask/ltspice.json",
    "https://formulae.brew.sh/api/cask/microsoft-excel.json",
    "https://formulae.brew.sh/api/cask/microsoft-onenote.json",
    "https://formulae.brew.sh/api/cask/microsoft-openjdk.json",
    "https://formulae.brew.sh/api/cask/microsoft-outlook.json",
    "https://formulae.brew.sh/api/cask/microsoft-powerpoint.json",
    "https://formulae.brew.sh/api/cask/microsoft-word.json",
    "https://formulae.brew.sh/api/cask/naps2.json",
    "https://formulae.brew.sh/api/cask/okta-verify.json",
    "https://formulae.brew.sh/api/cask/opencloud.json",
    "https://formulae.brew.sh/api/cask/opentoonz.json",
    "https://formulae.brew.sh/api/cask/osquery.json",
    "https://formulae.brew.sh/api/cask/outset.json",
    "https://formulae.brew.sh/api/cask/owncloud.json",
    "https://formulae.brew.sh/api/cask/purevpn.json",
    "https://formulae.brew.sh/api/cask/radio-silence.json",
    "https://formulae.brew.sh/api/cask/ringcentral.json",
    "https://formulae.brew.sh/api/cask/rocketman-choices-packager.json",
    "https://formulae.brew.sh/api/cask/salesforce-cli.json",
    "https://formulae.brew.sh/api/cask/securesafe.json",
    "https://formulae.brew.sh/api/cask/send-to-kindle.json",
    "https://formulae.brew.sh/api/cask/shutter-encoder.json",
    "https://formulae.brew.sh/api/cask/spyder.json",
    "https://formulae.brew.sh/api/cask/supportcompanion.json",
    "https://formulae.brew.sh/api/cask/swiftdialog.json",
    "https://formulae.brew.sh/api/cask/tableau-public.json",
    "https://formulae.brew.sh/api/cask/tableau-reader.json",
    "https://formulae.brew.sh/api/cask/teamviewer.json",
    "https://formulae.brew.sh/api/cask/topaz-photo-ai.json",
    "https://formulae.brew.sh/api/cask/topaz-video-ai.json",
    "https://formulae.brew.sh/api/cask/weasis.json",
    "https://formulae.brew.sh/api/cask/xquartz.json",
    "https://formulae.brew.sh/api/cask/insta360-link-controller.json",
    "https://formulae.brew.sh/api/cask/toshiba-color-mfp.json",
    "https://formulae.brew.sh/api/cask/perimeter81.json",
]

# Custom scraper scripts to run
custom_scrapers = [
    ".github/scripts/scrapers/remotehelp.sh",
    ".github/scripts/scrapers/starface.sh"
]

def calculate_file_hash(url):
    """Download a file and calculate its SHA256 hash."""
    print(f"📥 Downloading file from {url} to calculate hash...")
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            # Download the file in chunks
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Write the file in chunks
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            
            temp_file.flush()
            
            # Calculate SHA256 hash
            sha256_hash = hashlib.sha256()
            with open(temp_file.name, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
        
        except Exception as e:
            print(f"❌ Error calculating hash: {str(e)}")
            return None
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                print(f"Warning: Could not delete temporary file: {str(e)}")

def find_bundle_id(json_string):
    regex_patterns = {
        'pkgutil': r'(?s)"pkgutil"\s*:\s*(?:\[\s*"([^"]+)"(?:,\s*"([^"]+)")?\s*\]|\s*"([^"]+)")',
        'quit': r'(?s)"quit"\s*:\s*(?:\[\s*"([^"]+)"(?:,\s*"([^"]+)")?\s*\]|\s*"([^"]+)")',
        'launchctl': r'(?s)"launchctl"\s*:\s*(?:\[\s*"([^"]+)"(?:,\s*"([^"]+)")?\s*\]|\s*"([^"]+)")'
    }

    for key, pattern in regex_patterns.items():
        match = re.search(pattern, json_string)
        if match:
            if match.group(1):
                return match.group(1)
            elif match.group(3):
                return match.group(3)

    return None

def get_homebrew_app_info(json_url, needs_packaging=False, is_pkg_in_dmg=False, is_pkg_in_pkg=False, is_pkg=False):
    response = requests.get(json_url)
    response.raise_for_status()
    data = response.json()
    json_string = json.dumps(data)

    bundle_id = find_bundle_id(json_string)

    # Clean up version string by removing anything after the comma or underscore
    version = data["version"]
    if ',' in version:
        version = version.split(',')[0]
    if '_' in version:
        version = version.split('_')[0]

    url = data["url"]

    # Special URL handling for apps with non-working Homebrew URLs
    app_name = data["name"][0].lower()
    if app_name == "warp":
        # Warp's Homebrew URL returns HTML, use direct DMG URL instead
        url = f"https://releases.warp.dev/stable/v{version}/Warp.dmg"

    app_info = {
        "name": data["name"][0],
        "description": data["desc"],
        "version": version,
        "url": url,
        "bundleId": bundle_id,
        "homepage": data["homepage"],
        "fileName": get_filename_from_url(url, app_name=data["name"][0], version=version)
    }

    if needs_packaging:
        app_info["type"] = "app"
    elif is_pkg_in_dmg:
        app_info["type"] = "pkg_in_dmg"
    elif is_pkg_in_pkg:
        app_info["type"] = "pkg_in_pkg"
    elif is_pkg:
        app_info["type"] = "pkg"

    return app_info

def sanitize_filename(name):
    sanitized = name.replace(' ', '_')
    sanitized = re.sub(r'[^\w_]', '', sanitized)
    return sanitized.lower()

def update_readme_apps(apps_list):
    readme_path = Path(__file__).parent.parent.parent / "README.md"
    logos_path = Path(__file__).parent.parent.parent / "Logos"
    if not readme_path.exists():
        print("README.md not found")
        return

    print(f"\n📋 Checking logos for all apps...")
    print(f"Looking in: {logos_path}\n")

    # Read all app JSON files to get versions
    apps_folder = Path(__file__).parent.parent.parent / "Apps"
    apps_info = []
    missing_logos = []
    
    for app_json in apps_folder.glob("*.json"):
        # Read the JSON file to get the display name
        with open(app_json, 'r') as f:
            try:
                data = json.load(f)
                display_name = data['name']
                # Convert display name to filename format
                logo_name = sanitize_filename(display_name)
                
                # Look for matching logo file (trying both .png and .ico)
                logo_file = None
                for ext in ['.png', '.ico']:
                    # Case-insensitive search for logo files
                    potential_logos = [f for f in os.listdir(logos_path) 
                                     if f.lower() == f"{logo_name}{ext}".lower()]
                    if potential_logos:
                        logo_file = f"Logos/{potential_logos[0]}"
                        break
                
                if not logo_file:
                    missing_logos.append(display_name)

                apps_info.append({
                    'name': display_name,
                    'version': data['version'],
                    'logo': logo_file
                })
            except Exception as e:
                print(f"Error reading {app_json}: {e}")

    # Print missing logos summary
    if missing_logos:
        print("❌ Missing logos for the following apps:")
        for app in missing_logos:
            print(f"   - {app}")
        print("\nExpected logo files (case-insensitive):")
        for app in missing_logos:
            logo_name = sanitize_filename(app)
            print(f"   - {logo_name}.png or {logo_name}.ico")
        print("\n")
    else:
        print("✅ All apps have logos!\n")

    # Sort apps by name
    apps_info.sort(key=lambda x: x['name'].lower())

    # Create the new table content
    table_content = """### 📱 Supported Applications

| Application | Latest Version |
|-------------|----------------|
"""
    
    for app in apps_info:
        logo_cell = f"<img src='{app['logo']}' width='32' height='32'>" if app['logo'] else "❌"
        table_content += f"| {logo_cell} {app['name']} | {app['version']} |\n"

    # Add note about requesting new apps
    table_content += "\n> [!NOTE]\n"
    table_content += "> Missing an app? Feel free to [request additional app support]"
    table_content += "(https://github.com/ugurkocde/IntuneBrew/issues/new?labels=app-request) by creating an issue!\n"

    # Read the entire README
    with open(readme_path, 'r') as f:
        content = f.read()

    # Find the supported applications section using the correct marker
    start_marker = "### 📱 Supported Applications"
    end_marker = "## 🔧 Configuration"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("Couldn't find the markers in README.md")
        print(f"Start marker found: {start_idx != -1}")
        print(f"End marker found: {end_idx != -1}")
        return

    # Construct the new content
    new_content = (
        content[:start_idx] +
        table_content +
        "\n" +
        content[end_idx:]
    )

    # Write the updated content back to README.md
    with open(readme_path, 'w') as f:
        f.write(new_content)
    print("README.md has been updated with the new table format including logos")

def update_readme_with_latest_changes(apps_info):
    readme_path = Path(__file__).parent.parent.parent / "README.md"
    
    # Read current README content
    with open(readme_path, 'r') as f:
        content = f.read()

    # Prepare the updates section
    updates_section = "\n## 🔄 Latest Updates\n\n"
    updates_section += f"*Last checked: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*\n\n"

    # Get version changes
    version_changes = []
    for app in apps_info:
        try:
            with open(f"Apps/{sanitize_filename(app['name'])}.json", 'r') as f:
                current_data = json.load(f)
                if 'previous_version' in current_data and current_data['version'] != current_data['previous_version']:
                    version_changes.append({
                        'name': app['name'],
                        'old_version': current_data['previous_version'],
                        'new_version': current_data['version']
                    })
        except Exception as e:
            print(f"Error checking version history for {app['name']}: {e}")

    if version_changes:
        updates_section += "| Application | Previous Version | New Version |\n"
        updates_section += "|-------------|-----------------|-------------|\n"
        for change in version_changes:
            updates_section += f"| {change['name']} | {change['old_version']} | {change['new_version']} |\n"
    else:
        updates_section += "> All applications are up to date! 🎉\n"

    # Find where to insert the updates section (before the Features section)
    features_section = "## ✨ Features"
    
    if features_section in content:
        parts = content.split(features_section, 1)
        if len(parts) == 2:
            # Remove existing updates section if it exists
            if "## 🔄 Latest Updates" in parts[0]:
                # Find the start of the updates section
                updates_start = parts[0].find("## 🔄 Latest Updates")
                # Find the last newline before the updates section
                last_newline = parts[0].rfind("\n\n", 0, updates_start)
                if last_newline != -1:
                    # Keep everything before the updates section
                    parts[0] = parts[0][:last_newline] + "\n\n"
            
            # Construct new content with updates section in the new location
            new_content = (
                parts[0] +
                updates_section +
                features_section +
                parts[1]
            )
            
            # Write the updated content back to README.md
            with open(readme_path, 'w') as f:
                f.write(new_content)
            print(f"Updated README.md with latest changes and timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
            return
    
    print("Could not find the Features section in README.md")

def main():
    apps_folder = "Apps"
    os.makedirs(apps_folder, exist_ok=True)
    print(f"\n📁 Apps folder absolute path: {os.path.abspath(apps_folder)}")
    print(f"📁 Apps folder exists: {os.path.exists(apps_folder)}")
    print(f"📁 Apps folder is writable: {os.access(apps_folder, os.W_OK)}\n")
    
    supported_apps = []
    apps_info = []

    # Process apps that need special packaging
    for url in app_urls:
        try:
            print(f"\nProcessing special app URL: {url}")
            app_info = get_homebrew_app_info(url, needs_packaging=True)
            display_name = app_info['name']
            print(f"Got app info for: {display_name}")
            supported_apps.append(display_name)
            file_name = f"{sanitize_filename(display_name)}.json"
            print(f"🔍 Sanitized filename: {file_name}")
            file_path = os.path.join(apps_folder, file_name)
            print(f"📝 Attempting to write to: {os.path.abspath(file_path)}")

            # For existing files, update version, url, and recalculate SHA if version changed
            if os.path.exists(file_path):
                print(f"Found existing file for {display_name}")
                with open(file_path, "r") as f:
                    existing_data = json.load(f)
                    # Store the new version and check if it changed
                    new_version = app_info["version"]
                    version_changed = existing_data.get("version") != new_version
                    
                    # Always update version and url
                    existing_data["version"] = new_version
                    existing_data["url"] = app_info["url"]
                    
                    # For repackaged apps (type "app", "pkg_in_dmg", or "pkg_in_pkg"),
                    # preserve the fileName field from the existing JSON file
                    if "type" in existing_data and existing_data["type"] in ["app", "pkg_in_dmg", "pkg_in_pkg"]:
                        # Keep existing fileName for repackaged apps
                        if "fileName" in existing_data:
                            app_info["fileName"] = existing_data["fileName"]
                    else:
                        # For non-repackaged apps, update fileName to match the URL
                        existing_data["fileName"] = get_filename_from_url(app_info["url"], app_name=display_name, version=new_version)
                    
                    existing_data["previous_version"] = existing_data.get("version", "")
                    
                    # Calculate new hash if version changed
                    if version_changed:
                        print(f"🔍 Version changed, calculating new SHA256 hash for {display_name}...")
                        file_hash = calculate_file_hash(app_info["url"])
                        if file_hash:
                            existing_data["sha"] = file_hash
                            print(f"✅ New SHA256 hash calculated: {file_hash}")
                        else:
                            print(f"⚠️ Could not calculate SHA256 hash for {display_name}")
                    
                    # Update app_info with all existing data
                    app_info = existing_data

            with open(file_path, "w") as f:
                json.dump(app_info, f, indent=2)
                print(f"Successfully wrote {file_path} with type 'app' flag")

            apps_info.append(app_info)
            print(f"Saved app information for {display_name} to {file_path}")
        except Exception as e:
            print(f"Error processing special app {url}: {str(e)}")
            print(f"Full error details: ", e)

    # Process regular Homebrew cask URLs
    for url in homebrew_cask_urls:
        try:
            app_info = get_homebrew_app_info(url)
            display_name = app_info['name']
            supported_apps.append(display_name)
            file_name = f"{sanitize_filename(display_name)}.json"
            file_path = os.path.join(apps_folder, file_name)

            # Check if we need to calculate hash
            needs_hash = True
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    existing_data = json.load(f)
                    # Only calculate hash if:
                    # 1. No sha exists, or
                    # 2. Version has changed
                    if ("sha" in existing_data and
                        existing_data.get("version") == app_info["version"]):
                        needs_hash = False
                        app_info["sha"] = existing_data["sha"]
                        print(f"ℹ️ Using existing hash for {display_name}")

            if needs_hash:
                print(f"🔍 Calculating SHA256 hash for {display_name}...")
                file_hash = calculate_file_hash(app_info["url"])
                if file_hash:
                    app_info["sha"] = file_hash
                    print(f"✅ SHA256 hash calculated: {file_hash}")
                else:
                    print(f"⚠️ Could not calculate SHA256 hash for {display_name}")

            # For existing files, preserve existing data and update necessary fields
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    existing_data = json.load(f)
                    # Store the new version, url, sha and previous_version
                    new_version = app_info["version"]
                    new_url = app_info["url"]
                    new_sha = app_info.get("sha")
                    previous_version = existing_data.get("version")
                    
                    # Preserve all existing data except version, url, sha, and previous_version
                    for key in existing_data:
                        if key not in ["version", "url", "sha", "previous_version"]:
                            app_info[key] = existing_data[key]
                    
                    # Update version, url, sha and previous_version
                    app_info["version"] = new_version
                    app_info["url"] = new_url
                    
                    # Handle fileName field
                    if display_name.lower().replace(" ", "_") in preserve_filename_apps:
                        # For apps in the exclusion list, preserve the existing fileName
                        print(f"⚠️ Preserving custom fileName for {display_name}")
                    else:
                        # For all other apps, update fileName to match the URL
                        app_info["fileName"] = get_filename_from_url(new_url, app_name=display_name, version=new_version)
                    if new_sha:
                        app_info["sha"] = new_sha
                    app_info["previous_version"] = previous_version

            with open(file_path, "w") as f:
                json.dump(app_info, f, indent=2)

            apps_info.append(app_info)
            print(f"Saved app information for {display_name} to {file_path}")
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")

    # Process pkg_in_pkg apps
    for url in pkg_in_pkg_urls:
        try:
            print(f"\nProcessing PKG in PKG app URL: {url}")
            app_info = get_homebrew_app_info(url, is_pkg_in_pkg=True)
            display_name = app_info['name']
            supported_apps.append(display_name)
            file_name = f"{sanitize_filename(display_name)}.json"
            file_path = os.path.join(apps_folder, file_name)

            # For existing files, only update version, url and previous_version
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    existing_data = json.load(f)
                    # Store the new version, url and previous_version
                    new_version = app_info["version"]
                    new_url = app_info["url"]
                    previous_version = existing_data.get("version")
                    
                    # Preserve all existing data except version, url and previous_version
                    for key in existing_data:
                        if key not in ["version", "url", "previous_version"]:
                            app_info[key] = existing_data[key]
                    
                    # Update version, url and previous_version
                    app_info["version"] = new_version
                    app_info["url"] = new_url
                    
                    # Handle fileName field
                    if display_name.lower().replace(" ", "_") in preserve_filename_apps:
                        # For apps in the exclusion list, preserve the existing fileName
                        print(f"⚠️ Preserving custom fileName for {display_name}")
                    else:
                        # For all other apps, update fileName to match the URL
                        app_info["fileName"] = get_filename_from_url(new_url, app_name=display_name, version=new_version)
                    # Ensure fileName is preserved
                    app_info["previous_version"] = previous_version

            with open(file_path, "w") as f:
                json.dump(app_info, f, indent=2)

            apps_info.append(app_info)
            print(f"Saved app information for {display_name} to {file_path}")
        except Exception as e:
            print(f"Error processing PKG in PKG app {url}: {str(e)}")

    # Process direct pkg apps
    for url in pkg_urls:
        try:
            print(f"\nProcessing direct PKG app URL: {url}")
            app_info = get_homebrew_app_info(url, is_pkg=True)
            display_name = app_info['name']
            supported_apps.append(display_name)
            file_name = f"{sanitize_filename(display_name)}.json"
            file_path = os.path.join(apps_folder, file_name)

            # Check if we need to calculate hash for PKG apps
            needs_hash = True
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    existing_data = json.load(f)
                    # Only calculate hash if:
                    # 1. No sha exists, or
                    # 2. Version has changed
                    if ("sha" in existing_data and
                        existing_data.get("version") == app_info["version"]):
                        needs_hash = False
                        app_info["sha"] = existing_data["sha"]
                        print(f"ℹ️ Using existing hash for {display_name}")

            if needs_hash:
                print(f"🔍 Calculating SHA256 hash for {display_name}...")
                file_hash = calculate_file_hash(app_info["url"])
                if file_hash:
                    app_info["sha"] = file_hash
                    print(f"✅ SHA256 hash calculated: {file_hash}")
                else:
                    print(f"⚠️ Could not calculate SHA256 hash for {display_name}")

            # For existing files, preserve existing data and update necessary fields
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    existing_data = json.load(f)
                    # Store the new version, url, sha and previous_version
                    new_version = app_info["version"]
                    new_url = app_info["url"]
                    new_sha = app_info.get("sha")
                    previous_version = existing_data.get("version")
                    
                    # Preserve all existing data except version, url, sha and previous_version
                    for key in existing_data:
                        if key not in ["version", "url", "sha", "previous_version"]:
                            app_info[key] = existing_data[key]
                    
                    # Update version, url, sha and previous_version
                    app_info["version"] = new_version
                    app_info["url"] = new_url
                    if new_sha:
                        app_info["sha"] = new_sha
                    
                    # Handle fileName field
                    if display_name.lower().replace(" ", "_") in preserve_filename_apps:
                        # For apps in the exclusion list, preserve the existing fileName
                        print(f"⚠️ Preserving custom fileName for {display_name}")
                    else:
                        # For all other apps, update fileName to match the URL
                        app_info["fileName"] = get_filename_from_url(new_url, app_name=display_name, version=new_version)
                    app_info["previous_version"] = previous_version

            with open(file_path, "w") as f:
                json.dump(app_info, f, indent=2)

            apps_info.append(app_info)
            print(f"Saved app information for {display_name} to {file_path}")
        except Exception as e:
            print(f"Error processing direct PKG app {url}: {str(e)}")

    # Process pkg_in_dmg apps
    for url in pkg_in_dmg_urls:
        try:
            print(f"\nProcessing PKG in DMG app URL: {url}")
            app_info = get_homebrew_app_info(url, is_pkg_in_dmg=True)
            display_name = app_info['name']
            supported_apps.append(display_name)
            file_name = f"{sanitize_filename(display_name)}.json"
            file_path = os.path.join(apps_folder, file_name)

            # For existing files, only update version, url and previous_version
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    existing_data = json.load(f)
                    # Store the new version, url and previous_version
                    new_version = app_info["version"]
                    new_url = app_info["url"]
                    previous_version = existing_data.get("version")
                    
                    # Preserve all existing data except version, url and previous_version
                    for key in existing_data:
                        if key not in ["version", "url", "previous_version"]:
                            app_info[key] = existing_data[key]
                    
                    # Update version, url and previous_version
                    app_info["version"] = new_version
                    app_info["url"] = new_url
                    
                    # Handle fileName field
                    if display_name.lower().replace(" ", "_") in preserve_filename_apps:
                        # For apps in the exclusion list, preserve the existing fileName
                        print(f"⚠️ Preserving custom fileName for {display_name}")
                    else:
                        # For all other apps, update fileName to match the URL
                        app_info["fileName"] = get_filename_from_url(new_url, app_name=display_name, version=new_version)
                    app_info["previous_version"] = previous_version

            with open(file_path, "w") as f:
                json.dump(app_info, f, indent=2)

            apps_info.append(app_info)
            print(f"Saved app information for {display_name} to {file_path}")
        except Exception as e:
            print(f"Error processing PKG in DMG app {url}: {str(e)}")

    # Run custom scrapers and update apps_info accordingly
    for scraper in custom_scrapers:
        try:
            subprocess.run([scraper], check=True)
            # Get the app name from the JSON file created by the scraper
            json_file = os.path.join(apps_folder, os.path.basename(scraper).replace('.sh', '.json'))
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    app_data = json.load(f)
                    supported_apps.append(app_data['name'])
        except Exception as e:
            print(f"Error running scraper {scraper}: {str(e)}")

    # After custom scrapers run, calculate hashes for direct downloads
    print("\n📊 Checking custom scraper outputs for missing hashes...")
    for scraper in custom_scrapers:
        json_file = os.path.join(apps_folder, os.path.basename(scraper).replace('.sh', '.json'))
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                app_data = json.load(f)
            
            # Check if it's a direct download (DMG/PKG) without a hash
            if ('url' in app_data and 
                'sha' not in app_data and 
                (app_data['url'].endswith('.dmg') or app_data['url'].endswith('.pkg'))):
                
                print(f"🔍 Calculating SHA256 hash for {app_data['name']}...")
                file_hash = calculate_file_hash(app_data['url'])
                if file_hash:
                    app_data['sha'] = file_hash
                    # Write back the updated JSON
                    with open(json_file, 'w') as f:
                        json.dump(app_data, f, indent=2)
                    print(f"✅ SHA256 hash added for {app_data['name']}: {file_hash}")
                else:
                    print(f"⚠️ Could not calculate SHA256 hash for {app_data['name']}")

    # Update the README with both the apps table and latest changes
    update_readme_apps(supported_apps)
    update_readme_with_latest_changes(apps_info)

if __name__ == "__main__":
    main()
