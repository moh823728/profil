"""
system_bot.py — النسخة المُعاد بناؤها v7.0 ✨
══════════════════════════════════════════════════════════════════════════════
System Bot Premium — بُني من الصفر بأسلوب بوت التذاكر الفاخر
══════════════════════════════════════════════════════════════════════════════

المميزات:
1.  واجهة Ticket-Style UI       → Embeds عريضة + فواصل + إيموجيات احترافية
2.  رسالة إعداد ثابتة           → تتحدث (Edit) مع كل خطوة بدل إرسال رسائل جديدة
3.  ترحيب سينمائي               → Pillow 1150×400، هالة 14 طبقة، خطوط 62px + 50px
4.  RoleSelect فقط              → لا كتابة أسماء رتب — قوائم اختيار في كل مكان
5.  زر [ 🏗️ تنفيذ وتثبيت ]  → ينشئ كاتيجوري + غرف + صلاحيات برمجياً
6.  /admin موحد                 → Select Menu بالأوامر + Hierarchy صارم
7.  نظام اللوق (v7)       → وضع موحد أو مخصص، إنشاء تلقائي للرومات
8.  config.json                 → كل الإعدادات محفوظة وتُقرأ عند on_ready
9.  Select Menu ذكي (v7)        → الخطوة 3 بقائمة واحدة تفتح واجهة كل ميزة + زر رجوع
10. الرتب التفاعلية (v6)        → نظام Self-Roles كامل بأزرار يضغطها الأعضاء
11. الرد التلقائي (v7)          → ردود على كلمات مفتاحية تُخزَّن في قاعدة البيانات
12. إصلاح Toggle (v7)           → كل وظيفة تتحقق من حالة الميزة قبل التنفيذ
13. لوق الصوت (v7)              → on_voice_state_update مع توجيه _smart_log
14. نظام الفواصل والمسؤولين   → ميزات إضافية من system_extensions.py

ملاحظة: تم حذف نظام التنبيهات (Alert System) — نُقل إلى بوت مستقل.
"""

import asyncio
import io
import re
import discord
from discord import app_commands
from discord.ext import commands
import emojis_config
import system_extensions
from discord.ui import View, Button, Modal, TextInput
import json
import os
import datetime
import traceback

# Import support URL function from store_bot
try:
    from store_bot import get_support_url
except ImportError:
    # Fallback if store_bot is not available
    def get_support_url() -> str:
        return os.environ.get("STORE_SUPPORT_URL", "https://discord.gg/52BRpC3HV")

# ── مكتبات اختيارية ───────────────────────────────────────────────────────────
try:
    import aiohttp
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False
    print("[SystemBot] تنبيه: pip install Pillow aiohttp — صور الترحيب معطّلة")

# ══════════════════════════════════════════════════════════════════════════════
# ألوان النظام
# ══════════════════════════════════════════════════════════════════════════════
class C:
    GOLD     = discord.Color.from_rgb(212, 175, 55)
    NAVY     = discord.Color.from_rgb(10,  30,  80)
    SUCCESS  = discord.Color.from_rgb(40,  180,  90)
    DANGER   = discord.Color.from_rgb(200,  50,  50)
    WARNING  = discord.Color.from_rgb(230, 160,  20)
    INFO     = discord.Color.from_rgb(60,  130, 210)
    GRAPHITE = discord.Color.from_rgb(35,   35,  45)
    PURPLE   = discord.Color.from_rgb(110,  60, 200)

# ══════════════════════════════════════════════════════════════════════════════
# إعدادات الكونفيج
# ══════════════════════════════════════════════════════════════════════════════
_BASE = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.join(_BASE, "assets")

# Create assets directory if it doesn't exist
if not os.path.exists(_ASSETS_DIR):
    os.makedirs(_ASSETS_DIR)

_DEFAULTS = {
    # قنوات
    "setup_channel":        0,
    "welcome_channel":      0,
    "log_channel":          0,   # روم اللوق الموحد (حذف/تعديل/خروج)
    "sanctions_log_channel":0,   # روم لوق العقوبات
    # رتب متعددة
    "owner_roles":          [],
    "admin_roles":          [],
    "manager_roles":        [],
    "member_roles":         [],
    "interactive_roles":    [],   # رتب تفاعلية يختارها الأعضاء
    # mute role
    "mute_role":            0,
    "mute_channel_id":      0,
    # jail role
    "jail_role_id":         0,
    "jail_channel_id":      0,
    # jail customization
    "jail_custom_title":    "سجن",
    "jail_action_name":     "حبس",
    # auto-role
    "auto_role":            0,
    # ميزات
    "feature_welcome":      False,
    "feature_log":          False,
    "feature_sanctions":    False,
    "feature_auto_role":    False,
    "feature_self_roles":   False,
    "feature_auto_mod":     False,
    "feature_reaction_room": False,
    "feature_auto_reply":   False,
    "feature_separators":   False,
    # إعدادات الرتب التفاعلية
    "self_roles_channel":   0,
    "self_roles_config":    {},   # {role_id: {"label": str, "emoji": str, "description": str}}
    # ── نظام الرياكشن (Reaction Room Unlock) ─────────────────────────
    "reaction_room_channel": 0,
    "reaction_room_writer_role": 0,
    "reaction_room_emoji": "",
    "reaction_room_member_role": 0,
    "reaction_room_backup": {},  # {member_id: [role_ids]}
    "reaction_room_message_id": 0,
    "reaction_room_enabled": False,
    # ترحيب
    "welcome_bg_url":       "",
    "welcome_bg_url_fallback": "",  # Fallback URL for Discord CDN
    "welcome_msg":          "اهلاً {user} في {server}",
    "welcome_custom_msg":   "",
    "welcome_custom_msg_enabled": False,
    "welcome_enabled":      False,
    "welcome_channel":      "",
    "welcome_avatar_x":     None,       # X position for avatar center (None = center)
    "welcome_avatar_y":     None,       # Y position for avatar center (None = center)
    "welcome_avatar_size":  200,        # Avatar size in pixels
    "welcome_avatar_border": 10,        # Avatar border thickness
    "welcome_avatar_mask":  "circle",   # Avatar mask: "circle" or "square"
    "welcome_border_radius": 20,        # Image border radius
    "welcome_border_thickness": 5,        # Image border thickness
    # بناء مؤجل
    "build_done":           False,
    # ── ميزة الرد التلقائي (Auto-Response) ────────────────────────────────
    # Always active - no feature toggle needed
    "auto_responses":       {},   # {"keyword": "reply_text", ...}
    # ── نظام الحماية (Auto-Mod) ───────────────────────────────────────────
    "prohibited_words":     [],
    "punishment_config":    {
        "action": "timeout",
        "duration": "30m",
        "reason": "مخالفة نظام الحماية",
        "link_prefixes": []
    },
    # ── نظام اللوق المطوّر (Logs) ───────────────────────────────────
    "log_mode":             "unified",  # "unified" | "detailed"
    "log_category_id":      0,
    # ── Sanction Presets (for select menu) ───────────────────────────────
    "sanction_presets":      [
        {"reason": "إزعاج الشات", "duration": "1h"},
        {"reason": "مخالفة القوانين", "duration": "6h"},
        {"reason": "سب وقذ", "duration": "12h"},
        {"reason": "إهانة", "duration": "24h"},
        {"reason": "مخالفة متكررة", "duration": "3d"},
        {"reason": "أسباب مشروعة", "duration": "7d"},
    ],
    "log_voice_channel":    0,
    "log_chat_channel":     0,
    "log_admin_channel":    0,
    "log_join_leave_ch":    0,
}

MAX_TIMEOUT_SECONDS = 40320 * 60  # 28 يوم (الحد الأقصى لـ Discord Timeout)
DEFAULT_TEMPBAN_SECONDS = 86400   # 24 ساعة

ROLE_CATEGORIES = {
    "admin":       {"label": "Bot Manager",  "cfg_key": "admin_roles", "emoji_key": "bot_manager"},
    "manager":     {"label": "Admins",        "cfg_key": "manager_roles", "emoji_key": "admins"},
    "member":      {"label": "Member",        "cfg_key": "member_roles", "emoji_key": "members"},
    "interactive": {"label": "رول تفاعلي",  "cfg_key": "interactive_roles", "emoji_key": None},
}

# فئات صلاحيات الرتب فقط (بدون owner وبدون admin/Bot Manager)
PERMS_CATEGORIES = {
    "manager":     {"label": "🔧 Admins",        "cfg_key": "manager_roles"},
    "member":      {"label": "👤 Member",        "cfg_key": "member_roles"},
    "interactive": {"label": "🎭 رول تفاعلي",  "cfg_key": "interactive_roles"},
}

# ── قراءة وكتابة الكونفيج ─────────────────────────────────────────────────────
def _cfg_file(bot_dir=None):
    return os.path.join(bot_dir or _BASE, "system_config.json")

def cfg(key, bot_dir=None):
    """Safe JSON config loading with corruption recovery"""
    try:
        f = _cfg_file(bot_dir)
        if os.path.isfile(f):
            # Check if file is empty
            if os.path.getsize(f) == 0:
                print(f"[SystemBot] ⚠️ Config file is empty, attempting recovery from backup")
                return _recover_config(f, key)
            
            with open(f, "r", encoding="utf-8") as fp:
                return json.load(fp).get(key, _DEFAULTS.get(key))
    except json.JSONDecodeError as e:
        print(f"[SystemBot] ⚠️ JSON decode error: {e}, attempting recovery")
        f = _cfg_file(bot_dir)
        return _recover_config(f, key)
    except Exception as e:
        print(f"[SystemBot] ⚠️ Config load error: {e}")
    return _DEFAULTS.get(key)

def _recover_config(config_file: str, key: str):
    """Attempt to recover config from backup or initialize defaults"""
    try:
        # Try backup file first
        backup_file = config_file + ".bak"
        if os.path.isfile(backup_file) and os.path.getsize(backup_file) > 0:
            print(f"[SystemBot] 🔄 Recovering from backup: {backup_file}")
            with open(backup_file, "r", encoding="utf-8") as fp:
                return json.load(fp).get(key, _DEFAULTS.get(key))
    except Exception as e:
        print(f"[SystemBot] ⚠️ Backup recovery failed: {e}")
    
    # Return default value if recovery fails
    print(f"[SystemBot] 📋 Using default value for key: {key}")
    return _DEFAULTS.get(key)

def set_cfg(key, val, bot_dir=None):
    """Atomic file writing to prevent corruption"""
    f = _cfg_file(bot_dir)
    temp_f = f + ".tmp"
    backup_f = f + ".bak"
    
    try:
        # Load existing data safely
        data = {}
        if os.path.isfile(f):
            if os.path.getsize(f) > 0:
                try:
                    with open(f, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                except json.JSONDecodeError as e:
                    print(f"[SystemBot] ⚠️ Config corrupted during save, using backup: {e}")
                    if os.path.isfile(backup_f) and os.path.getsize(backup_f) > 0:
                        with open(backup_f, "r", encoding="utf-8") as fp:
                            data = json.load(fp)
                    else:
                        data = {}
        
        # Update data
        data[key] = val
        
        # Write to temporary file first (atomic operation)
        with open(temp_f, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
            fp.flush()
            os.fsync(fp.fileno())  # Ensure data is written to disk
        
        # Create backup of current file if it exists
        if os.path.isfile(f):
            try:
                if os.path.isfile(backup_f):
                    os.remove(backup_f)
                os.rename(f, backup_f)
            except Exception as e:
                print(f"[SystemBot] ⚠️ Backup creation failed: {e}")
        
        # Atomically replace the original file
        os.rename(temp_f, f)
        
    except Exception as e:
        print(f"[SystemBot] ❌ خطأ set_cfg: {e}")
        # Clean up temp file if it exists
        if os.path.isfile(temp_f):
            try:
                os.remove(temp_f)
            except:
                pass

def reload_config_for(bot):
    bd = bot._bot_dir
    bot.SETUP_CH         = int(cfg("setup_channel",         bd) or 0)
    bot.WELCOME_CH       = int(cfg("welcome_channel",        bd) or 0)
    bot.LOG_CH           = int(cfg("log_channel",            bd) or 0)
    bot.SANCTIONS_LOG_CH = int(cfg("sanctions_log_channel",  bd) or 0)
    bot.AUTO_ROLE        = int(cfg("auto_role",               bd) or 0)
    bot.LOG_VOICE_CH     = int(cfg("log_voice_channel",       bd) or 0)
    bot.LOG_CHAT_CH      = int(cfg("log_chat_channel",        bd) or 0)
    bot.LOG_ADMIN_CH     = int(cfg("log_admin_channel",       bd) or 0)
    bot.LOG_JOIN_LEAVE_CH= int(cfg("log_join_leave_ch",       bd) or 0)
    bot.JAIL_ROLE_ID     = int(cfg("jail_role_id",            bd) or 0)
    bot.JAIL_CHANNEL_ID = int(cfg("jail_channel_id",         bd) or 0)
    bot.JAIL_CUSTOM_TITLE= cfg("jail_custom_title",          bd) or "سجن"
    bot.JAIL_ACTION_NAME = cfg("jail_action_name",           bd) or "حبس"
    bot.REACTION_ROOM_CH = int(cfg("reaction_room_channel",   bd) or 0)
    bot.REACTION_ROOM_WRITER_ROLE = int(cfg("reaction_room_writer_role", bd) or 0)
    bot.REACTION_ROOM_EMOJI = cfg("reaction_room_emoji",     bd) or ""
    bot.REACTION_ROOM_MEMBER_ROLE = int(cfg("reaction_room_member_role", bd) or 0)
    bot.FEATURE_SEPARATORS = bool(cfg("feature_separators",  bd) or False)
    bot.prohibited_words = []
    for w in (cfg("prohibited_words", bd) or []):
        w_clean = str(w).strip().lower()
        if w_clean:
            bot.prohibited_words.append(w_clean)
    bot._prohibited_word_patterns = []
    for w in bot.prohibited_words:
        if " " in w:
            bot._prohibited_word_patterns.append(w)
        else:
            bot._prohibited_word_patterns.append(re.compile(rf"(?:^|\W){re.escape(w)}(?:$|\W)"))
    bot.punishment_config = cfg("punishment_config",          bd) or {}
    if isinstance(bot.punishment_config, dict):
        bot.punishment_config["action"] = _normalize_punishment_action(bot.punishment_config.get("action"))
        links = bot.punishment_config.get("link_prefixes", []) or []
        cleaned_links = []
        for link in links:
            link_clean = str(link).strip().lower()
            if link_clean:
                cleaned_links.append(link_clean)
        bot.punishment_config["link_prefixes"] = cleaned_links

def get_role_list(cat_key: str, bot_dir=None) -> list[int]:
    cfg_key = ROLE_CATEGORIES[cat_key]["cfg_key"]
    data = cfg(cfg_key, bot_dir)
    if isinstance(data, list):
        return [int(x) for x in data if x]
    elif data:
        return [int(data)]
    return []

def add_role(cat_key: str, role_id: int, bot_dir=None):
    cfg_key = ROLE_CATEGORIES[cat_key]["cfg_key"]
    current = get_role_list(cat_key, bot_dir)
    if role_id not in current:
        current.append(role_id)
    set_cfg(cfg_key, current, bot_dir)

def remove_role(cat_key: str, role_id: int, bot_dir=None):
    cfg_key = ROLE_CATEGORIES[cat_key]["cfg_key"]
    current = get_role_list(cat_key, bot_dir)
    current = [r for r in current if r != role_id]
    set_cfg(cfg_key, current, bot_dir)

def _now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d  %H:%M")

def _sep():
    return "\n\n── ── ── ── ── ── ── ── ──\n\n"

def _normalize_list(raw: str) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"[,\n،]+", raw)
    seen = set()
    out = []
    for part in parts:
        item = part.strip().lower()
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out

def _parse_duration_seconds(raw: str) -> int:
    if not raw:
        return 0
    text = raw.strip().lower()
    if not text:
        return 0
    # وحدات الوقت: s=ثانية، min=دقيقة، h=ساعة، d=يوم، m=شهر
    # First try to match 'min' for minutes to avoid conflict with 'm' for months
    matches = re.findall(r"(\d+)\s*(min|h|d|m|s)", text)
    if matches:
        total = 0
        mult = {"s": 1, "min": 60, "h": 3600, "d": 86400, "m": 2592000}  # m = 30 days (month)
        for num, unit in matches:
            total += int(num) * mult.get(unit, 0)
        return total
    # بدون وحدة → افتراض دقائق
    try:
        # Check if it's just a number, treat as minutes
        return int(text) * 60
    except ValueError:
        return 0

def _format_duration(seconds: int) -> str:
    if seconds <= 0:
        return "—"
    mins = seconds // 60
    days, rem_mins = divmod(mins, 1440)
    hours, mins = divmod(rem_mins, 60)
    parts = []
    if days:
        parts.append(f"{days} يوم")
    if hours:
        parts.append(f"{hours} ساعة")
    if mins or not parts:
        parts.append(f"{mins} دقيقة")
    return " ".join(parts)

def _normalize_punishment_action(raw: str) -> str:
    text = (raw or "").strip().lower()
    if text in {"ban", "باند", "حظر", "حظرنهائي", "حظر نهائي"}:
        return "ban"
    if text in {"timeout", "time out", "تيم اوت", "تيم أوت", "سجن", "jail"}:
        return "timeout"
    return "timeout"

def _punishment_label(action: str) -> str:
    return "🔨 باند" if action == "ban" else "⏱️ تيم أوت / سجن"

# ══════════════════════════════════════════════════════════════════════════════
# Hierarchy & Permission Helpers
# ══════════════════════════════════════════════════════════════════════════════
async def _resolve_member(guild: discord.Guild, raw: str):
    raw = raw.strip().lstrip("<@!").rstrip(">")
    try:
        uid = int(raw)
        m = guild.get_member(uid)
        if not m:
            try:
                m = await guild.fetch_member(uid)
            except Exception:
                pass
        return m
    except ValueError:
        return None

async def _send_log(guild: discord.Guild, log_ch_id: int, content: str):
    if not log_ch_id:
        return
    ch = guild.get_channel(log_ch_id)
    if ch:
        try:
            # تأكد أن content نص صريح فقط، لا embed
            if isinstance(content, discord.Embed):
                # لا تحول الـ Embed إلى str، تجاهله بدلاً من ذلك
                return
            await ch.send(content)
        except Exception:
            pass

def _embed_to_text(embed: discord.Embed) -> str:
    """Convert embed to simple text format"""
    lines = []
    if embed.title:
        lines.append(f"**{embed.title}**")
    if embed.description:
        lines.append(embed.description)
    for field in embed.fields:
        lines.append(f"**{field.name}**: {field.value}")
    if embed.footer:
        lines.append(embed.footer.text)
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════════════════════
# Sanction Select Menu View (40-second timeout with preset reasons)
# ══════════════════════════════════════════════════════════════════════════════
class SanctionSelectView(View):
    def __init__(self, bot_ref, original_message: discord.Message, target: discord.Member,
                 sanction_type: str, admin: discord.Member, revert_func, bot_dir: str):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.original_message = original_message
        self.target = target
        self.sanction_type = sanction_type
        self.admin = admin
        self.revert_func = revert_func
        self.bot_dir = bot_dir
        self._selected = False

        # Load presets from config
        presets = cfg("sanction_presets", bot_dir) or []
        options = []
        for preset in presets:
            reason = preset.get("reason", "بدون سبب")
            duration = preset.get("duration", "1h")
            label = f"{reason} ({duration})"
            options.append(discord.SelectOption(label=label, value=f"{reason}|{duration}"))

        select = discord.ui.Select(
            placeholder="اختر السبب والمدة...",
            options=options[:25],  # Discord limit
            custom_id="sanction_select_v2"
        )
        select.callback = self._on_select
        self.add_item(select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the command issuer to interact with this view"""
        return interaction.user.id == self.admin.id

    async def _on_select(self, interaction: discord.Interaction):
        self._selected = True
        self.stop()
        
        selected_value = interaction.data["values"][0]
        reason, duration = selected_value.split("|", 1)
        
        # Remove from pending tracking
        if hasattr(self.bot, '_pending_sanctions') and self.original_message.id in self.bot._pending_sanctions:
            del self.bot._pending_sanctions[self.original_message.id]
        
        # Delete the select menu message
        try:
            await interaction.message.delete()
        except Exception:
            pass
        
        # Add reaction to original command message
        try:
            await self.original_message.add_reaction("✅")
        except Exception:
            pass
        
        # Log the sanction
        guild = self.original_message.guild
        bd = self.bot_dir
        log_content = f"""-------------------------------
# لوق {self.sanction_type}
المسؤول: {self.admin.mention}
المعاقب: {self.target.mention}
العقوبه: {self.sanction_type}
السبب: {reason}
المدة: {duration}
-------------------------------"""
        await _smart_log(guild, bd, "sanctions", log_content)
        
        # Schedule auto-removal if duration is specified
        dur_secs = _parse_duration_seconds(duration)
        if dur_secs > 0:
            async def _auto_remove():
                await asyncio.sleep(dur_secs)
                try:
                    await self.revert_func()
                    log_revert = f"""-------------------------------
# لوق إلغاء {self.sanction_type}
المعاقب: {self.target.mention}
انتهت المدة: {duration}
الحالة: تم إلغاء العقوبة تلقائياً
-------------------------------"""
                    await _smart_log(guild, bd, "sanctions", log_revert)
                except Exception:
                    pass
            asyncio.create_task(_auto_remove())

    async def on_timeout(self):
        if not self._selected:
            # Remove from pending tracking
            if hasattr(self.bot, '_pending_sanctions') and self.original_message.id in self.bot._pending_sanctions:
                del self.bot._pending_sanctions[self.original_message.id]
            
            # Revert the action silently
            try:
                await self.revert_func()
            except Exception:
                pass
            
            # Delete the select menu message silently (no notification)
            try:
                await self.message.delete()
            except Exception:
                pass

async def _smart_log(guild: discord.Guild, bot_dir, log_type: str, content: str):
    """
    نظام اللوق — يوجّه اللوق للروم الصحيح تبعاً للوضع.
    log_type: "voice" | "chat" | "admin" | "join_leave" | "sanctions"
    """
    if not bool(cfg("feature_log", bot_dir)):
        return
    # تأكد أن content نص صريح فقط، لا embed
    if isinstance(content, discord.Embed):
        return
    mode = cfg("log_mode", bot_dir) or "unified"
    if mode == "detailed":
        key_map = {
            "voice":      "log_voice_channel",
            "chat":       "log_chat_channel",
            "admin":      "log_admin_channel",
            "join_leave": "log_join_leave_ch",
            "sanctions":  "log_sanctions_channel",
        }
        ch_id = int(cfg(key_map.get(log_type, "log_channel"), bot_dir) or 0)
    else:
        ch_id = int(cfg("log_channel", bot_dir) or 0)
    await _send_log(guild, ch_id, content)

# ══════════════════════════════════════════════════════════════════════════════
# Leave Roles Memory
# ══════════════════════════════════════════════════════════════════════════════
def _roles_file(bot_dir=None):
    return os.path.join(bot_dir or _BASE, "leave_roles_memory.json")

# ══════════════════════════════════════════════════════════════════════════════
# Mute/Jail Role Backup System
# ══════════════════════════════════════════════════════════════════════════════
def _punishment_roles_file(bot_dir=None):
    return os.path.join(bot_dir or _BASE, "punishment_roles_backup.json")

def save_muted_user_roles(member: discord.Member, bot_dir=None) -> list:
    """Save user's current roles before muting (excluding @everyone, managed/bot roles, and roles above bot)"""
    f = _punishment_roles_file(bot_dir)
    try:
        data = {}
        if os.path.isfile(f):
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        
        # Filter roles: exclude @everyone, managed, bot integration, and roles above bot's top role
        bot_top_role = member.guild.me.top_role if member.guild.me else None
        role_ids = []
        for r in member.roles:
            if r.is_default() or r.managed:
                continue
            if bot_top_role and r.position >= bot_top_role.position:
                continue
            role_ids.append(r.id)
        
        data[str(member.id)] = role_ids
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)
        return role_ids
    except Exception as e:
        print(f"[SystemBot] Error saving muted user roles for {member.display_name}: {e}")
        return []

def load_muted_user_roles(member_id: int, bot_dir=None) -> list:
    """Load saved roles for a muted user"""
    f = _punishment_roles_file(bot_dir)
    try:
        if os.path.isfile(f):
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                user_id_str = str(member_id)
                saved_ids = data.get(user_id_str, [])
                print(f"[DEBUG] load_muted_user_roles: member_id={member_id}, user_id_str={user_id_str}, saved_ids={saved_ids}")
                return saved_ids
    except Exception as e:
        print(f"[DEBUG] load_muted_user_roles ERROR: {e}")
        pass
    return []

def clear_muted_user_roles(member_id: int, bot_dir=None):
    """Clear saved roles for a muted user after unmute"""
    f = _punishment_roles_file(bot_dir)
    try:
        if os.path.isfile(f):
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            data.pop(str(member_id), None)
            with open(f, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)
    except Exception:
        pass

def save_jailed_user_roles(member: discord.Member, bot_dir=None) -> list:
    """Save user's current roles before jailing (excluding @everyone, managed/bot roles, and roles above bot)"""
    f = _punishment_roles_file(bot_dir)
    try:
        data = {}
        if os.path.isfile(f):
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        
        # Filter roles: exclude @everyone, managed, bot integration, and roles above bot's top role
        bot_top_role = member.guild.me.top_role if member.guild.me else None
        role_ids = []
        for r in member.roles:
            if r.is_default() or r.managed:
                continue
            if bot_top_role and r.position >= bot_top_role.position:
                continue
            role_ids.append(r.id)
        
        # Store in jailed_users_roles section
        if "jailed_users_roles" not in data:
            data["jailed_users_roles"] = {}
        data["jailed_users_roles"][str(member.id)] = role_ids
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)
        return role_ids
    except Exception as e:
        print(f"[SystemBot] Error saving jailed user roles for {member.display_name}: {e}")
        return []

def load_jailed_user_roles(member_id: int, bot_dir=None) -> list:
    """Load saved roles for a jailed user"""
    f = _punishment_roles_file(bot_dir)
    try:
        if os.path.isfile(f):
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                user_id_str = str(member_id)
                saved_ids = data.get("jailed_users_roles", {}).get(user_id_str, [])
                print(f"[DEBUG] load_jailed_user_roles: member_id={member_id}, user_id_str={user_id_str}, saved_ids={saved_ids}")
                return saved_ids
    except Exception as e:
        print(f"[DEBUG] load_jailed_user_roles ERROR: {e}")
        pass
    return []

def clear_jailed_user_roles(member_id: int, bot_dir=None):
    """Clear saved roles for a jailed user after unjail"""
    f = _punishment_roles_file(bot_dir)
    try:
        if os.path.isfile(f):
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            if "jailed_users_roles" in data:
                data["jailed_users_roles"].pop(str(member_id), None)
            with open(f, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)
    except Exception:
        pass

def save_member_roles(member: discord.Member, bot_dir=None) -> list:
    f = _roles_file(bot_dir)
    try:
        data = {}
        if os.path.isfile(f):
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        role_ids = [r.id for r in member.roles if not r.is_default() and not r.managed]
        data[str(member.id)] = role_ids
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)
        return role_ids
    except Exception:
        return []

def load_member_roles(member_id: int, bot_dir=None) -> list:
    f = _roles_file(bot_dir)
    try:
        if os.path.isfile(f):
            with open(f, "r", encoding="utf-8") as fp:
                return json.load(fp).get(str(member_id), [])
    except Exception:
        pass
    return []

def clear_member_roles(member_id: int, bot_dir=None):
    f = _roles_file(bot_dir)
    try:
        if os.path.isfile(f):
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            data.pop(str(member_id), None)
            with open(f, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
# Welcome Image Generator — Pillow الأصلي مُستعاد
# ══════════════════════════════════════════════════════════════════════════════
async def _fetch_bytes(url: str) -> bytes | None:
    if not url:
        return None
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    return await r.read()
    except Exception as ex:
        print(f"[SystemBot] fetch error for {url}: {ex}")
    return None

def _guild_cfg(key: str, guild_id: int, bot_dir) -> any:
    """Get config value with guild-specific key"""
    guild_key = f"{key}_{guild_id}"
    return cfg(guild_key, bot_dir)

def _set_guild_cfg(key: str, guild_id: int, value, bot_dir):
    """Set config value with guild-specific key"""
    guild_key = f"{key}_{guild_id}"
    set_cfg(guild_key, value, bot_dir)

def _strip_emoji(text: str) -> str:
    return re.sub(
        "["
        "\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
        "\U00002500-\U00002BEF\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", "", text, flags=re.UNICODE).strip()

# ══════════════════════════════════════════════════════════════════════════════
# Server Images Mapping - JSON Storage for Guild-Specific Image Links
# ══════════════════════════════════════════════════════════════════════════════
_SERVER_IMAGES_FILE = os.path.join(_BASE, "server_images.json")

def _read_server_images() -> dict:
    """Read server_images.json and return guild image links mapping"""
    try:
        if os.path.exists(_SERVER_IMAGES_FILE):
            with open(_SERVER_IMAGES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as ex:
        print(f"[Server Images] Error reading file: {ex}")
    return {}

def _write_server_images(data: dict) -> bool:
    """Write guild image links mapping to server_images.json"""
    try:
        with open(_SERVER_IMAGES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as ex:
        print(f"[Server Images] Error writing file: {ex}")
        return False

def _get_guild_image_url(guild_id: int) -> str | None:
    """Get welcome background URL for specific guild from server_images.json"""
    data = _read_server_images()
    guild_key = str(guild_id)
    if guild_key in data:
        return data[guild_key].get("welcome_bg_url")
    return None

def _set_guild_image_url(guild_id: int, url: str) -> bool:
    """Set welcome background URL for specific guild in server_images.json"""
    data = _read_server_images()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = {}
    data[guild_key]["welcome_bg_url"] = url
    return _write_server_images(data)

def _get_guild_dm_info(guild_id: int) -> tuple[int, int] | None:
    """Get DM channel_id and message_id for specific guild from server_images.json"""
    data = _read_server_images()
    guild_key = str(guild_id)
    if guild_key in data:
        channel_id = data[guild_key].get("dm_channel_id")
        message_id = data[guild_key].get("dm_message_id")
        if channel_id and message_id:
            return (int(channel_id), int(message_id))
    return None

def _set_guild_dm_info(guild_id: int, channel_id: int, message_id: int) -> bool:
    """Set DM channel_id and message_id for specific guild in server_images.json"""
    data = _read_server_images()
    guild_key = str(guild_id)
    if guild_key not in data:
        data[guild_key] = {}
    data[guild_key]["dm_channel_id"] = channel_id
    data[guild_key]["dm_message_id"] = message_id
    return _write_server_images(data)

# ══════════════════════════════════════════════════════════════════════════════
# New Welcome Card System V2 - Completely Rewritten
# ══════════════════════════════════════════════════════════════════════════════

async def v2_fetch_background_image(guild_id: int, bot_dir: str, bot: commands.Bot) -> bytes | None:
    """Fetch background image from unified storage - NO FALLBACK - Returns None on error"""
    try:
        # Try to get URL from server_images.json (unified structure)
        bg_url = _get_guild_image_url(guild_id)
        if bg_url:
            image_bytes = await _fetch_bytes(bg_url)
            if image_bytes:
                return image_bytes
            else:
                print(f"[V2 Welcome] Error: Failed to fetch background from URL {bg_url} for guild {guild_id}")
        else:
            print(f"[V2 Welcome] Error: No background URL found in server_images.json for guild {guild_id}")
        
        # Try to get DM info from server_images.json
        dm_info = _get_guild_dm_info(guild_id)
        if dm_info:
            channel_id, message_id = dm_info
            # Fetch the DM channel
            channel = bot.get_channel(channel_id)
            if channel:
                # Fetch the message
                message = await channel.fetch_message(message_id)
                if message and message.attachments:
                    # Get the image URL from the attachment
                    image_url = message.attachments[0].url
                    image_bytes = await _fetch_bytes(image_url)
                    if image_bytes:
                        return image_bytes
                else:
                    print(f"[V2 Welcome] Error: DM message found but no attachments for guild {guild_id}")
            else:
                print(f"[V2 Welcome] Error: DM channel {channel_id} not found for guild {guild_id}")
        else:
            print(f"[V2 Welcome] Error: No DM info found in server_images.json for guild {guild_id}")
        
        # Fallback to local file
        bg_path = os.path.join(_ASSETS_DIR, f"welcome_bg_{guild_id}.png")
        if os.path.exists(bg_path):
            with open(bg_path, "rb") as f:
                return f.read()
        else:
            print(f"[V2 Welcome] Error: No local background file found at {bg_path} for guild {guild_id}")
        
        # No background found - return None
        return None
            
    except Exception as ex:
        print(f"[V2 Welcome] CRITICAL Error fetching bg for guild {guild_id}: {ex}")
        import traceback
        traceback.print_exc()
        return None

async def v2_save_background_image(guild_id: int, image_url: str, bot_dir: str, bot: commands.Bot) -> bool:
    """Save background image to DM storage - Single Image Per Server"""
    try:
        # Try to get bot owner for DM storage
        dm_channel = None
        try:
            if bot.application_info:
                app_info = await bot.application_info()
                if app_info.owner:
                    dm_channel = await app_info.owner.create_dm()
        except Exception as owner_ex:
            print(f"[V2 Welcome] Could not get bot owner for DM: {owner_ex}")
        
        # Fallback to log channel if available
        if not dm_channel:
            log_ch_id = cfg("log_channel", bot_dir)
            if log_ch_id:
                # This won't be a DM channel, but we can still store the image there
                try:
                    dm_channel = bot.get_channel(log_ch_id)
                except Exception as log_ex:
                    print(f"[V2 Welcome] Could not get log channel: {log_ex}")
        
        # Delete old DM message if exists
        old_dm_info = _get_guild_dm_info(guild_id)
        if old_dm_info and dm_channel:
            old_channel_id, old_message_id = old_dm_info
            try:
                old_channel = bot.get_channel(old_channel_id)
                if old_channel:
                    old_message = await old_channel.fetch_message(old_message_id)
                    await old_message.delete()
                    print(f"[V2 Welcome] Deleted old DM message for guild {guild_id}")
            except Exception as ex:
                print(f"[V2 Welcome] Error deleting old DM message: {ex}")
        
        # Download the image
        image_bytes = await _fetch_bytes(image_url)
        if not image_bytes:
            return False
        
        # Send the image to DM (if we have a valid channel)
        dm_message = None
        if dm_channel:
            try:
                file = discord.File(io.BytesIO(image_bytes), filename=f"welcome_bg_{guild_id}.png")
                dm_message = await dm_channel.send(file=file)
                print(f"[V2 Welcome] Sent image to DM/log channel for guild {guild_id}")
            except Exception as send_ex:
                print(f"[V2 Welcome] Could not send to DM/log channel: {send_ex}")
                dm_channel = None  # Mark as unavailable
        
        # Save DM info to server_images.json (only if we successfully sent to DM)
        if dm_channel and dm_message:
            dm_saved = _set_guild_dm_info(guild_id, dm_channel.id, dm_message.id)
            if not dm_saved:
                print(f"[V2 Welcome] Failed to save DM info for guild {guild_id}")
        else:
            print(f"[V2 Welcome] No DM message sent, skipping DM info save for guild {guild_id}")
        
        # Save URL to server_images.json in unified structure (always save the URL)
        url_saved = _set_guild_image_url(guild_id, image_url)
        if not url_saved:
            print(f"[V2 Welcome] Failed to save URL to server_images.json for guild {guild_id}")
        
        # Delete old local image for this guild if exists
        old_bg_path = os.path.join(_ASSETS_DIR, f"welcome_bg_{guild_id}.png")
        if os.path.exists(old_bg_path):
            try:
                os.remove(old_bg_path)
                print(f"[V2 Welcome] Deleted old local bg for guild {guild_id}")
            except Exception as ex:
                print(f"[V2 Welcome] Error deleting old local bg: {ex}")
        
        # Save locally as backup using absolute path
        new_bg_path = os.path.abspath(os.path.join(_ASSETS_DIR, f"welcome_bg_{guild_id}.png"))
        if PILLOW_OK:
            try:
                img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
                with open(new_bg_path, "wb") as f:
                    img.save(f, format="PNG")
                print(f"[V2 Welcome] Saved local backup for guild {guild_id}")
            except Exception as ex:
                print(f"[V2 Welcome] Pillow conversion error: {ex}")
                # Fallback to raw bytes
                with open(new_bg_path, "wb") as f:
                    f.write(image_bytes)
        else:
            # No Pillow - save raw bytes
            with open(new_bg_path, "wb") as f:
                f.write(image_bytes)
        
        print(f"[V2 Welcome] Saved bg to DM for guild {guild_id}")
        return True
    except Exception as ex:
        print(f"[V2 Welcome] Error saving bg for guild {guild_id}: {ex}")
        import traceback
        traceback.print_exc()
        return False

def v2_cleanup_duplicate_backgrounds():
    """Clean up duplicate background images - keep only newest per guild"""
    try:
        if not os.path.exists(_ASSETS_DIR):
            return
        
        # Group files by guild_id
        guild_files = {}
        for filename in os.listdir(_ASSETS_DIR):
            if filename.startswith("welcome_bg_") and filename.endswith(".png"):
                # Extract guild_id from filename
                parts = filename.replace("welcome_bg_", "").replace(".png", "").split("_")
                if len(parts) >= 1:
                    try:
                        guild_id = parts[0]
                        filepath = os.path.join(_ASSETS_DIR, filename)
                        mtime = os.path.getmtime(filepath)
                        
                        if guild_id not in guild_files:
                            guild_files[guild_id] = []
                        guild_files[guild_id].append((filepath, mtime))
                    except Exception:
                        pass
        
        # Keep only newest file per guild
        for guild_id, files in guild_files.items():
            if len(files) > 1:
                # Sort by modification time (newest first)
                files.sort(key=lambda x: x[1], reverse=True)
                # Keep first (newest), delete rest
                for filepath, _ in files[1:]:
                    try:
                        os.remove(filepath)
                        print(f"[V2 Welcome Cleanup] Deleted duplicate for guild {guild_id}: {filepath}")
                    except Exception as ex:
                        print(f"[V2 Welcome Cleanup] Error deleting {filepath}: {ex}")
        
        print(f"[V2 Welcome Cleanup] Completed - checked {len(guild_files)} guilds")
    except Exception as ex:
        print(f"[V2 Welcome Cleanup] Error: {ex}")

async def v2_generate_welcome_card(avatar_url: str, bg_bytes: bytes, avatar_size: int = 200,
                                   avatar_x: int = None, avatar_y: int = None) -> bytes | None:
    """Generate welcome card with avatar only - NO TEXT - Preserves original image dimensions and transparency - Returns None on error"""
    if not bg_bytes:
        print("[V2 Welcome] Error: No background bytes provided")
        return None

    if not avatar_url:
        print("[V2 Welcome] Error: No avatar URL provided")
        return None

    try:
        # Open background image directly - preserve original dimensions and transparency
        img = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
        W, H = img.width, img.height

        # Fetch avatar bytes from URL
        avatar_bytes = await _fetch_bytes(avatar_url)
        if not avatar_bytes:
            print(f"[V2 Welcome] Error: Failed to fetch avatar from {avatar_url}")
            return None

        # Avatar setup - use provided coordinates or center by default
        if avatar_x is None:
            avatar_x = (W - avatar_size) // 2  # Center horizontally
        if avatar_y is None:
            avatar_y = (H - avatar_size) // 2  # Center vertically

        # Open and resize avatar with faster resampling
        av = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((avatar_size, avatar_size), Image.BILINEAR)

        # Create circular mask
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask).ellipse([(0, 0), (avatar_size, avatar_size)], fill=255)
        av.putalpha(mask)

        # Paste avatar at specified coordinates directly on background
        img.paste(av, (avatar_x, avatar_y), av)

        # Save as PNG without optimize for faster saving
        out = io.BytesIO()
        img.save(out, format="PNG")
        out.seek(0)
        return out.getvalue()

    except Exception as ex:
        print(f"[V2 Welcome] CRITICAL Error generating card: {ex}")
        import traceback
        traceback.print_exc()
        return None


class NewWelcomeCardSystem(View):
    """New Welcome System V2 - Completely Rewritten"""
    def __init__(self, bot_ref, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.is_shortcut = is_shortcut
        bd = bot_ref._bot_dir

        # Get emojis from config
        try:
            emoji_channel = emojis_config.WELCOME_EMOJIS["channel"]
            emoji_background = emojis_config.WELCOME_EMOJIS["background"]
            emoji_avatar_edit = emojis_config.WELCOME_EMOJIS["avatar_edit"]
            emoji_preview = emojis_config.WELCOME_EMOJIS["preview"]
        except Exception:
            emoji_channel = None
            emoji_background = None
            emoji_avatar_edit = None
            emoji_preview = None

        options = [
            discord.SelectOption(label="اختيار قناة الترحيب", value="channel",
                               description="اختر القناة التي تُرسل فيها الترحيبات", emoji=emoji_channel),
            discord.SelectOption(label="تعيين خلفية الترحيب", value="background",
                               description="رفع صورة كخلفية للترحيب", emoji=emoji_background),
            discord.SelectOption(label="تعديل الأفاتار", value="avatar_edit",
                               description="تحديد موقع وحجم الأفاتار", emoji=emoji_avatar_edit),
            discord.SelectOption(label="معاينة (Preview)", value="preview",
                               description="توليد صورة تجريبية للترحيب", emoji=emoji_preview),
        ]

        sel = discord.ui.Select(
            placeholder="اختر إعداد نظام الترحب...",
            options=options,
            custom_id="v2_welcome_main_sel",
            row=0
        )
        sel.callback = self._on_main_select
        self.add_item(sel)

    async def _on_main_select(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        
        choice = interaction.data["values"][0]

        if choice == "channel":
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **اختيار قناة الترحيب**\nاختر القناة من القائمة أدناه:",
                view=CustomChannelSelector(self.bot)
            )
        elif choice == "background":
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **تعيين خلفية الترحيب**\nارفع صورة الخلفية الجديدة:",
                view=NewWelcomeCardSystem(self.bot)
            )
            await interaction.followup.send("بانتظار رفع الصورة...", ephemeral=True)
            await self._v2_wait_for_image_upload(interaction)
        elif choice == "avatar_edit":
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **تعديل الأفاتار / النظام**\n\n🔗 **رابط المحرر:** https://moh823728.github.io/profil/\n\n📋 **التعليمات:\n1. افتح الرابط أعلاه في متصفحك\n2. قم بتخصيص الأفاتار والاسم والرسالة\n3. اضغط على \"نسخ الإعدادات والإحداثيات\"\n4. ارجع هنا واضغط **[ التالي ]** للصق الإعدادات",
                view=WelcomeEditorNavigationView(self.bot)
            )
        elif choice == "preview":
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **جاري توليد معاينة...**",
                view=NewWelcomeCardSystem(self.bot)
            )
            await interaction.followup.send("جاري التوليد...", ephemeral=True)
            await self._v2_preview_handler(interaction)

    async def _v2_wait_for_image_upload(self, interaction: discord.Interaction):
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id and m.attachments
        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            attachment = msg.attachments[0]
            if not attachment.content_type.startswith("image/"):
                await interaction.followup.send("❌ يجب إرسال صورة فقط.", ephemeral=True)
                await msg.delete()
                return
            
            bg_url = attachment.url
            guild_id = interaction.guild.id
            bd = self.bot._bot_dir
            
            # Save to DM storage (primary source of truth)
            saved = await v2_save_background_image(guild_id, bg_url, bd, self.bot)
            if saved:
                _set_guild_cfg("welcome_enabled", guild_id, True, bd)
                reload_config_for(self.bot)
                
                # Send immediate DM echo to user
                try:
                    dm_channel = await interaction.user.create_dm()
                    image_bytes = await _fetch_bytes(attachment.url)
                    if image_bytes:
                        file = discord.File(io.BytesIO(image_bytes), filename="welcome_bg_saved.png")
                        await dm_channel.send(
                            "✅ تم استلام خلفية الترحيب بنجاح! هذه الصورة هي النسخة المعتمدة حالياً لسيرفرك وسيتم التعديل عليها مباشرة.",
                            file=file
                        )
                except Exception as dm_ex:
                    print(f"[V2 Welcome] Failed to send DM echo: {dm_ex}")
                    # Fallback: send to log channel if available
                    log_ch_id = cfg("log_channel", bd)
                    if log_ch_id:
                        try:
                            log_ch = interaction.guild.get_channel(log_ch_id)
                            if log_ch:
                                image_bytes = await _fetch_bytes(attachment.url)
                                if image_bytes:
                                    file = discord.File(io.BytesIO(image_bytes), filename="welcome_bg_saved.png")
                                    await log_ch.send(
                                        f"✅ تم استلام خلفية الترحيب بنجاح لسيرفر {interaction.guild.name} من {interaction.user.mention}! هذه الصورة هي النسخة المعتمدة حالياً وسيتم التعديل عليها مباشرة.",
                                        file=file
                                    )
                        except Exception as log_ex:
                            print(f"[V2 Welcome] Failed to send to log channel: {log_ex}")
                
                await msg.delete()
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                    view=NewWelcomeCardSystem(self.bot)
                )
                await interaction.followup.send("تم حفظ الصورة بنجاح!", ephemeral=True)
            else:
                await interaction.followup.send("❌ فشل حفظ الصورة.", ephemeral=True)
                await msg.delete()
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ انتهت المهلة", ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                view=NewWelcomeCardSystem(self.bot)
            )
        except Exception as ex:
            await interaction.followup.send(f"❌ خطأ: {ex}", ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                view=NewWelcomeCardSystem(self.bot)
            )



    async def _v2_preview_handler(self, interaction: discord.Interaction):
        try:
            bd = self.bot._bot_dir
            guild = interaction.guild
            guild_id = guild.id
            
            # Check if guild has background URL in server_images.json
            bg_url = _get_guild_image_url(guild_id)
            if not bg_url:
                print(f"[V2 Welcome Preview] Error: No welcome_bg_url found in server_images.json for guild {guild_id}")
                import traceback
                traceback.print_exc()
                await interaction.followup.send("⚠️ يوجد خطأ: لم يتم رفع صورة خلفية لهذا السيرفر بعد، يرجى رفع صورة أولاً.", ephemeral=True)
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                    view=NewWelcomeCardSystem(self.bot)
                )
                return
            
            # Fetch background from unified storage - NO FALLBACK
            bg_bytes = await v2_fetch_background_image(guild_id, bd, self.bot)
            
            if not bg_bytes:
                print(f"[V2 Welcome Preview] Error: Failed to fetch background bytes for guild {guild_id}")
                import traceback
                traceback.print_exc()
                await interaction.followup.send("⚠️ يوجد خطأ: تعذر تحميل صورة الخلفية. راجع الـ Terminal للتفاصيل.", ephemeral=True)
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                    view=NewWelcomeCardSystem(self.bot)
                )
                return
            
            # Get avatar URL
            avatar_url = guild.me.display_avatar.with_format("png").url
            
            # Get custom coordinates and size from config
            avatar_x = _guild_cfg("welcome_avatar_x", guild_id, bd)
            avatar_y = _guild_cfg("welcome_avatar_y", guild_id, bd)
            avatar_size = _guild_cfg("welcome_avatar_size", guild_id, bd) or 200
            
            # Generate welcome card with avatar only and custom coordinates
            img_bytes = await v2_generate_welcome_card(avatar_url, bg_bytes, avatar_size, avatar_x, avatar_y)
            
            if not img_bytes:
                print(f"[V2 Welcome Preview] Error: Failed to generate welcome card for guild {guild_id}")
                import traceback
                traceback.print_exc()
                await interaction.followup.send("⚠️ يوجد خطأ: تعذر توليد بطاقة الترحيب. راجع الـ Terminal للتفاصيل.", ephemeral=True)
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                    view=NewWelcomeCardSystem(self.bot)
                )
                return
            
            # Send the preview image
            file = discord.File(io.BytesIO(img_bytes), filename="welcome_preview.png")
            await interaction.followup.send(file=file, ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                view=NewWelcomeCardSystem(self.bot)
            )
        except Exception as ex:
            print(f"[V2 Welcome] Preview error: {ex}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ خطأ في توليد المعاينة: {ex}", ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                view=NewWelcomeCardSystem(self.bot)
            )


class CustomChannelSelector(View):
    """Custom Channel Selector for Welcome System V2"""
    def __init__(self, bot_ref):
        super().__init__(timeout=None)
        self.bot = bot_ref
        
        ch_sel = discord.ui.ChannelSelect(
            channel_types=[discord.ChannelType.text],
            placeholder="اختر قناة الترحيب",
            custom_id="v2_welcome_ch_sel",
            row=0
        )
        ch_sel.callback = self._on_ch_select
        self.add_item(ch_sel)

    async def _on_ch_select(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        ch_id = int(interaction.data["values"][0])
        guild_id = interaction.guild.id
        bd = self.bot._bot_dir
        _set_guild_cfg("welcome_channel", guild_id, ch_id, bd)
        _set_guild_cfg("welcome_enabled", guild_id, True, bd)
        reload_config_for(self.bot)
        ch = interaction.guild.get_channel(ch_id)
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **إعداد نظام الترحب**",
            view=NewWelcomeCardSystem(self.bot)
        )
        await interaction.followup.send(
            f"تم حفظ القناة: {ch.mention if ch else ch_id}\nتم تفعيل نظام الترحب تلقائياً",
            ephemeral=True
        )


class CoordinateEditorModal(Modal, title="ضبط الإحداثيات"):
    """Coordinate Editor Modal for Welcome System V2"""
    def __init__(self, bot_ref, guild_id: int):
        super().__init__()
        self.bot = bot_ref
        self.guild_id = guild_id
        bd = bot_ref._bot_dir
        
        self.avatar_coords = TextInput(
            label="Avatar (X, Y) - اترك فارغاً للوسط",
            placeholder=f"{_guild_cfg('welcome_avatar_x', guild_id, bd) or ''}, {_guild_cfg('welcome_avatar_y', guild_id, bd) or ''}",
            default=f"{_guild_cfg('welcome_avatar_x', guild_id, bd) or ''}, {_guild_cfg('welcome_avatar_y', guild_id, bd) or ''}",
            required=False,
            max_length=20,
            row=0
        )
        self.avatar_size = TextInput(
            label="Avatar Size (Pixels)",
            placeholder=f"{_guild_cfg('welcome_avatar_size', guild_id, bd) or 200}",
            default=f"{_guild_cfg('welcome_avatar_size', guild_id, bd) or 200}",
            required=True,
            max_length=5,
            row=1
        )
        
        self.add_item(self.avatar_coords)
        self.add_item(self.avatar_size)
    
    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        
        try:
            bd = self.bot._bot_dir
            guild_id = self.guild_id
            
            # Parse avatar coordinates (optional)
            av_x = None
            av_y = None
            if self.avatar_coords.value.strip():
                av_parts = [x.strip() for x in self.avatar_coords.value.split(',')]
                if len(av_parts) == 2:
                    av_x = int(av_parts[0]) if av_parts[0] else None
                    av_y = int(av_parts[1]) if av_parts[1] else None
            
            # Parse avatar size (required)
            avatar_size = int(self.avatar_size.value) if self.avatar_size.value else 200
            
            _set_guild_cfg("welcome_avatar_x", guild_id, av_x, bd)
            _set_guild_cfg("welcome_avatar_y", guild_id, av_y, bd)
            _set_guild_cfg("welcome_avatar_size", guild_id, avatar_size, bd)
            reload_config_for(self.bot)
            
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                view=NewWelcomeCardSystem(self.bot)
            )
            await interaction.followup.send("تم تحديث الإحداثيات بنجاح!", ephemeral=True)
        except ValueError as ve:
            await interaction.response.send_message(f"❌ تنسيق غير صحيح: {ve}", ephemeral=True)
        except Exception as ex:
            await interaction.response.send_message(f"❌ خطأ: {ex}", ephemeral=True)


class WelcomeEditorNavigationView(View):
    """Navigation view for welcome editor with Next and Back buttons"""
    def __init__(self, bot_ref):
        super().__init__(timeout=None)
        self.bot = bot_ref

    @discord.ui.button(label="التالي", style=discord.ButtonStyle.success, custom_id="welcome_editor_next", row=0)
    async def next_btn(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("⛔ تحتاج صلاحية المدير.", ephemeral=True)
            return
        
        await interaction.response.send_modal(WelcomeJSONInputModal(self.bot, interaction.guild.id))

    @discord.ui.button(label="رجوع", style=discord.ButtonStyle.secondary, custom_id="welcome_editor_back", row=0)
    async def back_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **إعداد نظام الترحب**",
            view=NewWelcomeCardSystem(self.bot)
        )


class WelcomeJSONInputModal(Modal, title="إدخال إعدادات الترحيب"):
    """Modal for pasting JSON config from web editor"""
    def __init__(self, bot_ref, guild_id: int):
        super().__init__()
        self.bot = bot_ref
        self.guild_id = guild_id

        self.json_input = TextInput(
            label="ألصق إعدادات JSON هنا",
            placeholder='{"avatar": {"x": 120, "y": 80, "radius": 50}, ...}',
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=4000,
            row=0
        )
        self.add_item(self.json_input)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        
        try:
            bd = self.bot._bot_dir
            guild_id = self.guild_id
            
            # Parse JSON
            config = json.loads(self.json_input.value)
            
            # Validate and extract avatar settings
            avatar_config = config.get("avatar", {})
            avatar_x = avatar_config.get("x")
            avatar_y = avatar_config.get("y")
            avatar_radius = avatar_config.get("radius", 50)
            
            # Validate and extract username settings
            username_config = config.get("username", {})
            username_x = username_config.get("x")
            username_y = username_config.get("y")
            username_font_size = username_config.get("font_size", 32)
            username_color = username_config.get("color", "#FFFFFF")
            
            # Validate and extract canvas_text settings (NEW)
            canvas_text_config = config.get("canvas_text", {})
            canvas_text = canvas_text_config.get("text", "")
            canvas_text_x = canvas_text_config.get("x")
            canvas_text_y = canvas_text_config.get("y")
            canvas_text_font_size = canvas_text_config.get("font_size", 16)
            canvas_text_color = canvas_text_config.get("color", "#b9bbbe")
            
            # Validate and extract chat_message settings (NEW)
            chat_message_config = config.get("chat_message", {})
            chat_message_text = chat_message_config.get("text", "مرحباً بك في السيرفر!")
            
            # Extract mention settings
            mention_config = chat_message_config.get("mention", {})
            enable_mention = mention_config.get("enabled", True)
            mention_trigger = mention_config.get("trigger", "{mention}")
            
            # Extract owner mention settings (NEW)
            owner_config = chat_message_config.get("owner", {})
            enable_owner = owner_config.get("enabled", False)
            owner_trigger = owner_config.get("trigger", "{owner}")
            
            # Extract server mention settings (NEW)
            server_config = chat_message_config.get("server", {})
            enable_server = server_config.get("enabled", False)
            server_trigger = server_config.get("trigger", "")
            
            # Extract bold settings
            bold_config = chat_message_config.get("bold", {})
            enable_bold = bold_config.get("enabled", True)
            bold_trigger = bold_config.get("trigger", "")
            
            # Extract italic settings
            italic_config = chat_message_config.get("italic", {})
            enable_italic = italic_config.get("enabled", False)
            italic_trigger = italic_config.get("trigger", "")
            
            # Extract count settings
            count_config = chat_message_config.get("count", {})
            enable_count = count_config.get("enabled", False)
            count_trigger = count_config.get("trigger", "{count}")
            
            # Extract channel shortcuts settings (NEW)
            channel_shortcuts = chat_message_config.get("channel_shortcuts", [])
            
            # Save avatar settings
            _set_guild_cfg("welcome_avatar_x", guild_id, avatar_x, bd)
            _set_guild_cfg("welcome_avatar_y", guild_id, avatar_y, bd)
            _set_guild_cfg("welcome_avatar_size", guild_id, avatar_radius * 2, bd)  # Convert radius to size
            
            # Save chat message settings
            _set_guild_cfg("welcome_custom_msg", guild_id, chat_message_text, bd)
            _set_guild_cfg("welcome_custom_msg_enabled", guild_id, True, bd)
            _set_guild_cfg("welcome_msg", guild_id, chat_message_text, bd)
            
            # Store all formatting settings in a comprehensive config key
            formatting_config = {
                "username_x": username_x,
                "username_y": username_y,
                "username_font_size": username_font_size,
                "username_color": username_color,
                "canvas_text": canvas_text,
                "canvas_text_x": canvas_text_x,
                "canvas_text_y": canvas_text_y,
                "canvas_text_font_size": canvas_text_font_size,
                "canvas_text_color": canvas_text_color,
                "chat_message_text": chat_message_text,
                "enable_mention": enable_mention,
                "mention_trigger": mention_trigger,
                "enable_owner": enable_owner,
                "owner_trigger": owner_trigger,
                "enable_server": enable_server,
                "server_trigger": server_trigger,
                "enable_bold": enable_bold,
                "bold_trigger": bold_trigger,
                "enable_italic": enable_italic,
                "italic_trigger": italic_trigger,
                "enable_count": enable_count,
                "count_trigger": count_trigger,
                "channel_shortcuts": channel_shortcuts
            }
            _set_guild_cfg("welcome_formatting", guild_id, formatting_config, bd)
            
            # Enable welcome feature
            _set_guild_cfg("welcome_enabled", guild_id, True, bd)
            _set_guild_cfg("feature_welcome", guild_id, True, bd)
            
            reload_config_for(self.bot)
            
            # Clean success message and auto-return to main menu
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                view=NewWelcomeCardSystem(self.bot)
            )
            await interaction.followup.send("تم الإعداد بنجاح!", ephemeral=True)
            
        except json.JSONDecodeError:
            await interaction.response.send_message("❌ تنسيق JSON غير صحيح. تأكد من نسخ الإعدادات بشكل صحيح من المحرر.", ephemeral=True)
        except Exception as ex:
            await interaction.response.send_message(f"❌ خطأ في حفظ الإعدادات: {ex}", ephemeral=True)


# ══════════════════════════════════════════════════════════════════════════════
# Embed Builder — Ticket-Style
# ══════════════════════════════════════════════════════════════════════════════
def _embed(title: str, desc: str, color=None,
           footer: str = "System Bot  •  Premium v6.0") -> discord.Embed:
    e = discord.Embed(title=title, description=desc, color=color or C.GOLD)
    e.set_footer(text=footer)
    return e

def _roles_field_value(role_ids: list, guild: discord.Guild) -> str:
    if not role_ids:
        return "⬜  لم يُضبط بعد"
    mentions = [f"<@&{rid}>" for rid in role_ids if guild.get_role(rid)]
    return "  ".join(mentions) if mentions else "⬜  لم يُضبط بعد"

# ══════════════════════════════════════════════════════════════════════════════
# SECTION A — الشاشة الرئيسية (Hub)
# ══════════════════════════════════════════════════════════════════════════════
def _hub_embed(guild: discord.Guild) -> discord.Embed:
    owner_name = str(guild.owner) if guild.owner else "—"
    e = _embed(
        "🏰  System Bot Premium — لوحة الإعداد",
        f"**Owner** = {owner_name}\n\n"
        f"أهلاً وسهلاً يا صاحب هذا السيرفر الرائع،\n"
        f"يسعدنا أن نقدم لك **System Bot Premium** — البوت المتكامل الذي سيرفع سيرفرك لمستوى احترافي حقيقي.\n"
        f"من هنا تتحكم بكل شيء: الرتب، الميزات، اللوق، الإجازات، والأوامر الإدارية — كل ذلك بضغطة زر.\n"
        f"{_sep()}"
        f"**السيرفر:** {guild.name}\n"
        f"**الأعضاء:** {guild.member_count:,}\n"
        f"{_sep()}"
        "🚀 **ابدأ الإعداد** — ضبط الرتب والميزات خطوة بخطوة بكل سهولة.\n"
        "🛠️ **الدعم الفني** — تواصل معنا لأي استفسار أو مشكلة.",
        C.GOLD,
        footer=f"System Bot  •  v6.0  •  {guild.name}"
    )
    if guild.icon:
        e.set_thumbnail(url=guild.icon.url)
    return e


class HubView(View):
    def __init__(self, bot_ref, caller_id: int = None):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.caller_id = int(caller_id) if caller_id else None  # Track who summoned the command
        
        # Add support button dynamically with URL
        support_url = get_support_url()
        support_btn = discord.ui.Button(
            label="🛠️ الدعم الفني", 
            style=discord.ButtonStyle.link,
            url=support_url,
            row=0
        )
        self.add_item(support_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the caller to interact with this view"""
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "عفواً، هذه الواجهة مخصصة للشخص الذي استدعى الأمر فقط.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="بدء 🚀", style=discord.ButtonStyle.success,
                       custom_id="hub_start_btn_unique", row=0)
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button = None):
        # No defer needed - respond immediately to prevent "thinking" state
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **الخطوة 1: إعداد الرتب**\nاختر فئة الرتبة من القائمة:",
            view=Step1RolesView(self.bot, self.caller_id),
            embeds=[])

# ══════════════════════════════════════════════════════════════════════════════
# SECTION B — الخطوة 1: إعداد الرتب بـ RoleSelect
# ══════════════════════════════════════════════════════════════════════════════
def _step1_roles_embed(bot_ref, guild: discord.Guild) -> discord.Embed:
    bd = bot_ref._bot_dir
    lines = []
    for cat_key, cat_info in ROLE_CATEGORIES.items():
        if cat_key == "interactive":
            continue  # لا تُظهر الرتب التفاعلية هنا
        rids = get_role_list(cat_key, bd)
        val  = _roles_field_value(rids, guild)
        lines.append(f"**{cat_info['label']}** → {val}")
    return _embed(
        "⚙️  الخطوة 1 من 3  —  إعداد الرتب",
        "اختر فئة الرتبة من القائمة ثم اختر الرتبة من سيرفرك مباشرة.\n"
        "لا حاجة لكتابة أي شيء — فقط اختر من القوائم.\n"
        f"{_sep()}"
        + "\n".join(lines)
        + f"{_sep()}"
        "بعد الانتهاء اضغط **➡️ التالي** للانتقال لضبط الميزات.",
        C.NAVY,
        footer="System Bot  •  الخطوة 1 من 3  •  Role Setup"
    )


class Step1RolesView(View):
    def __init__(self, bot_ref, caller_id: int = None):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.caller_id = int(caller_id) if caller_id else None
        
        # Select لاختيار الفئة (بدون الرتب التفاعلية)
        cat_options = []
        for cat_key, info in ROLE_CATEGORIES.items():
            if cat_key == "interactive":
                continue  # لا تُظهر الرتب التفاعلية هنا
            
            # Get emoji from config or use default
            emoji = emojis_config.ROLE_CATEGORIES_EMOJIS.get(info["emoji_key"], "📋")
            
            cat_options.append(
                discord.SelectOption(
                    label=info["label"], 
                    value=cat_key,
                    description=f"إضافة رتبة لفئة {info['label']}",
                    emoji=emoji
                )
            )
        
        cat_sel = discord.ui.Select(
            placeholder="اختر فئة الرتبة...",
            options=cat_options, custom_id="s1_cat_sel_v5", row=0)
        cat_sel.callback = self._on_cat_select
        self.add_item(cat_sel)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the caller to interact with this view"""
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "عفواً، هذه الواجهة مخصصة للشخص الذي استدعى الأمر فقط.",
                ephemeral=True
            )
            return False
        return True

    async def _on_cat_select(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        cat_key = interaction.data["values"][0]
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **إدارة فئة {ROLE_CATEGORIES[cat_key]['label']}**\nاختر رتبة من السيرفر:",
            view=CatManageView(self.bot, cat_key, self.caller_id),
            embeds=[])

    @discord.ui.button(label="التالي", emoji=emojis_config.NAV_EMOJIS['next'], style=discord.ButtonStyle.success,
                       custom_id="step1_next_btn_unique", row=1)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button = None):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **الخطوة 2: تفعيل الميزات**\nاختر الميزة للتفعيل أو التعطيل:",
            view=Step2FeaturesView(self.bot, self.caller_id),
            embeds=[])


def _cat_manage_embed(bot_ref, cat_key: str, guild: discord.Guild) -> discord.Embed:
    info = ROLE_CATEGORIES[cat_key]
    rids = get_role_list(cat_key, bot_ref._bot_dir)
    val  = _roles_field_value(rids, guild)
    return _embed(
        f"🎭 إدارة فئة {info['label']}",
        f"اختر رتبة من السيرفر لإضافتها أو إزالتها.\n\n"
        f"**الرتب الحالية:** {val}",
        C.GOLD)


class CatManageView(View):
    def __init__(self, bot_ref, cat_key: str, caller_id: int = None):
        super().__init__(timeout=None)
        self.bot     = bot_ref
        self.cat_key = cat_key
        self.caller_id = int(caller_id) if caller_id else None
        
        # Get emojis from emoji_config
        add_emoji_str = emojis_config.GENERIC_EMOJIS.get("add_role", "✅")
        remove_emoji_str = emojis_config.GENERIC_EMOJIS.get("remove_role", "❌")
        back_emoji_str = emojis_config.NAV_EMOJIS.get("back", "◀")
        
        try:
            add_emoji = discord.PartialEmoji.from_str(add_emoji_str)
        except:
            add_emoji = add_emoji_str
            
        try:
            remove_emoji = discord.PartialEmoji.from_str(remove_emoji_str)
        except:
            remove_emoji = remove_emoji_str
            
        try:
            back_emoji = discord.PartialEmoji.from_str(back_emoji_str)
        except:
            back_emoji = back_emoji_str
        
        # 2-option Select Menu for Add/Remove Role
        options = [
            discord.SelectOption(
                label="إضافة رتبة",
                description="إضافة رتبة جديدة لهذه الفئة",
                emoji=add_emoji,
                value="add_role"
            ),
            discord.SelectOption(
                label="إزالة رتبة",
                description="عرض وحذف الرتب المضافة حالياً",
                emoji=remove_emoji,
                value="remove_role"
            )
        ]
        
        action_sel = discord.ui.Select(
            placeholder="اختر إجراء...",
            options=options,
            custom_id=f"cat_action_{cat_key}_v6",
            row=0
        )
        action_sel.callback = self._on_action_select
        self.add_item(action_sel)
        
        # Back button
        back_btn = discord.ui.Button(
            label="رجوع",
            emoji=back_emoji,
            style=discord.ButtonStyle.secondary,
            custom_id=f"cat_back_{cat_key}_v6",
            row=1
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    async def _on_action_select(self, interaction: discord.Interaction):
        action = interaction.data["values"][0]
        
        if action == "add_role":
            # Switch to Add Role view
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **إدارة فئة {ROLE_CATEGORIES[self.cat_key]['label']}**\nاختر رتبة أو أكثر للإضافة:",
                view=CatAddRoleView(self.bot, self.cat_key, self.caller_id),
                embeds=[]
            )
        elif action == "remove_role":
            # Check if there are roles to remove
            rids = get_role_list(self.cat_key, self.bot._bot_dir)
            if not rids:
                await interaction.response.send_message(
                    "لا توجد رتب مضافة حالياً في هذه الفئة.",
                    ephemeral=True
                )
                # Stay on the same view
                return
            
            # Switch to Remove Role view
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **إدارة فئة {ROLE_CATEGORIES[self.cat_key]['label']}**\nاختر رتبة للحذف:",
                view=CatRemoveRoleView(self.bot, self.cat_key, self.caller_id),
                embeds=[]
            )

    async def _on_back(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **الخطوة 1: إعداد الرتب**\nاختر فئة الرتبة من القائمة:",
            view=Step1RolesView(self.bot, self.caller_id),
            embeds=[]
        )


class CatAddRoleView(View):
    def __init__(self, bot_ref, cat_key: str, caller_id: int = None):
        super().__init__(timeout=None)
        self.bot     = bot_ref
        self.cat_key = cat_key
        self.caller_id = int(caller_id) if caller_id else None
        
        # Get back emoji from emoji_config
        back_emoji_str = emojis_config.NAV_EMOJIS.get("back", "◀")
        try:
            back_emoji = discord.PartialEmoji.from_str(back_emoji_str)
        except:
            back_emoji = back_emoji_str
        
        # Multi-select RoleSelect for adding roles
        role_add_sel = discord.ui.RoleSelect(
            placeholder="اختر رتبة أو أكثر للإضافة...",
            custom_id=f"cat_add_role_{cat_key}_v6",
            row=0,
            min_values=1, max_values=25
        )
        role_add_sel.callback = self._on_add
        self.add_item(role_add_sel)
        
        # Back button
        back_btn = discord.ui.Button(
            label="رجوع",
            emoji=back_emoji,
            style=discord.ButtonStyle.secondary,
            custom_id=f"cat_back_{cat_key}_v6",
            row=1
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    async def _on_add(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        if not _has_bot_manager_permission(interaction.user, self.bot._bot_dir):
            return await interaction.followup.send("⛔ ليس لديك الصلاحية.", ephemeral=True)
        
        added_mentions = []
        for role_raw in interaction.data["values"]:
            role_id = int(role_raw)
            add_role(self.cat_key, role_id, self.bot._bot_dir)
            role_obj = interaction.guild.get_role(role_id)
            added_mentions.append(role_obj.mention if role_obj else str(role_id))
        
        reload_config_for(self.bot)
        
        # Return to main category management view
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **إدارة فئة {ROLE_CATEGORIES[self.cat_key]['label']}**\nاختر إجراء:",
            view=CatManageView(self.bot, self.cat_key, self.caller_id),
            embeds=[]
        )
        
        await interaction.followup.send(
            embed=_embed("✅ تمت الإضافة",
                         f"تم إضافة {', '.join(added_mentions)} لفئة "
                         f"**{ROLE_CATEGORIES[self.cat_key]['label']}**", C.SUCCESS),
            ephemeral=True
        )

    async def _on_back(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **إدارة فئة {ROLE_CATEGORIES[self.cat_key]['label']}**\nاختر إجراء:",
            view=CatManageView(self.bot, self.cat_key, self.caller_id),
            embeds=[]
        )


class CatRemoveRoleView(View):
    def __init__(self, bot_ref, cat_key: str, caller_id: int = None):
        super().__init__(timeout=None)
        self.bot     = bot_ref
        self.cat_key = cat_key
        self.caller_id = int(caller_id) if caller_id else None
        
        # Get back emoji from emoji_config
        back_emoji_str = emojis_config.NAV_EMOJIS.get("back", "◀")
        try:
            back_emoji = discord.PartialEmoji.from_str(back_emoji_str)
        except:
            back_emoji = back_emoji_str
        
        # Get current roles for this category
        rids = get_role_list(self.cat_key, self.bot._bot_dir)
        
        if not rids:
            # No roles configured - only show back button
            self._no_roles = True
        else:
            self._no_roles = False
            options = []
            emoji_str = emojis_config.GENERIC_EMOJIS.get("role", "🎭")
            try:
                emoji = discord.PartialEmoji.from_str(emoji_str)
            except:
                emoji = emoji_str
            
            for rid in rids[:25]:
                # Try to resolve role across all guilds
                role = None
                if bot_ref.guilds:
                    for guild in bot_ref.guilds:
                        role = guild.get_role(rid)
                        if role:
                            break
                
                # Use role name if found, otherwise use fallback label
                if role:
                    label = role.name[:50]
                else:
                    label = f"رتبة محذوفة ({rid})"[:50]
                
                options.append(discord.SelectOption(label=label, value=str(rid), emoji=emoji))
            
            sel = discord.ui.Select(
                placeholder="اختر الرتبة للحذف...",
                options=options,
                custom_id=f"cat_rm_sel_{cat_key}_v6",
                row=0
            )
            sel.callback = self._on_select
            self.add_item(sel)
        
        # Back button (always present)
        back_btn = discord.ui.Button(
            label="رجوع",
            emoji=back_emoji,
            style=discord.ButtonStyle.secondary,
            custom_id=f"cat_back_{cat_key}_v6",
            row=1
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    async def _on_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if not _has_bot_manager_permission(interaction.user, self.bot._bot_dir):
            return await interaction.followup.send("⛔ ليس لديك الصلاحية.", ephemeral=True)
        
        role_id = int(interaction.data["values"][0])
        remove_role(self.cat_key, role_id, self.bot._bot_dir)
        
        # Return to main category management view
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **إدارة فئة {ROLE_CATEGORIES[self.cat_key]['label']}**\nاختر إجراء:",
            view=CatManageView(self.bot, self.cat_key, self.caller_id),
            embeds=[]
        )
        
        await interaction.followup.send(
            embed=_embed("✅ تم الحذف", "تمت إزالة الرتبة من الفئة.", C.SUCCESS),
            ephemeral=True
        )

    async def _on_back(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **إدارة فئة {ROLE_CATEGORIES[self.cat_key]['label']}**\nاختر إجراء:",
            view=CatManageView(self.bot, self.cat_key, self.caller_id),
            embeds=[]
        )

# ══════════════════════════════════════════════════════════════════════════════
# SECTION B-2 — صلاحيات الرتب (Discord Permissions Menu)
# ══════════════════════════════════════════════════════════════════════════════

# جميع الصلاحيات المتاحة في ديسكورد مقسّمة بشكل واضح
DISCORD_PERMISSIONS = [
    # ── عامة ──────────────────────────────────────────────────────────────────
    ("view_channel",              "👁️  رؤية القنوات"),
    ("manage_channels",           "🗂️  إدارة القنوات"),
    ("manage_roles",              "🎭  إدارة الرتب"),
    ("manage_expressions",        "😀  إدارة الإيموجي والستيكرز"),
    ("manage_webhooks",           "🔗  إدارة الويبهوك"),
    ("manage_guild",              "⚙️  إدارة السيرفر"),
    ("view_audit_log",            "📋  عرض سجل المراقبة"),
    ("view_guild_insights",       "📊  عرض إحصاءات السيرفر"),
    # ── عضوية ─────────────────────────────────────────────────────────────────
    ("create_instant_invite",     "📨  إنشاء دعوات"),
    ("change_nickname",           "✏️  تغيير الاسم المستعار"),
    ("manage_nicknames",          "📝  إدارة أسماء الأعضاء"),
    ("kick_members",              "👢  طرد الأعضاء"),
    ("ban_members",               "🔨  حظر الأعضاء"),
    ("moderate_members",          "⏱️  مؤقت العضو (Timeout)"),
    # ── نصي ───────────────────────────────────────────────────────────────────
    ("send_messages",             "💬  إرسال رسائل"),
    ("send_messages_in_threads",  "🧵  إرسال في الثردات"),
    ("create_public_threads",     "📂  إنشاء ثردات عامة"),
    ("create_private_threads",    "🔒  إنشاء ثردات خاصة"),
    ("embed_links",               "🔗  تضمين روابط"),
    ("attach_files",              "📎  إرفاق ملفات"),
    ("add_reactions",             "😄  إضافة تفاعلات"),
    ("use_external_emojis",       "🌐  استخدام إيموجي خارجي"),
    ("use_external_stickers",     "🎨  استخدام ستيكر خارجي"),
    ("mention_everyone",          "📢  منشن @everyone"),
    ("manage_messages",           "🗑️  إدارة الرسائل"),
    ("manage_threads",            "🧵  إدارة الثردات"),
    ("read_message_history",      "📜  قراءة سجل الرسائل"),
    ("send_tts_messages",         "🔊  إرسال رسائل TTS"),
    ("use_application_commands",  "🤖  استخدام أوامر التطبيقات"),
    # ── صوتي ──────────────────────────────────────────────────────────────────
    ("connect",                   "🎧  الاتصال بقنوات الصوت"),
    ("speak",                     "🎙️  التحدث في قنوات الصوت"),
    ("stream",                    "📺  البث المباشر"),
    ("use_embedded_activities",   "🎮  استخدام الأنشطة"),
    ("use_soundboard",            "🎵  استخدام لوح الأصوات"),
    ("use_external_sounds",       "🎶  استخدام أصوات خارجية"),
    ("priority_speaker",          "⭐  المتحدث ذو الأولوية"),
    ("mute_members",              "🔇  كتم الأعضاء"),
    ("deafen_members",            "🙉  صم الأعضاء"),
    ("move_members",              "🚚  نقل الأعضاء"),
    ("request_to_speak",          "🙋  طلب الكلام (المسرح)"),
    # ── إدارة متقدمة ──────────────────────────────────────────────────────────
    ("administrator",             "👑  مدير (كل الصلاحيات)"),
]

# مفتاح الكونفيج لحفظ الصلاحيات
# نحفظ: {"owner": [perm1, perm2], "admin": [...], ...}
PERMS_CFG_KEY = "role_permissions_config"


def _get_role_perms_cfg(bot_dir) -> dict:
    data = cfg(PERMS_CFG_KEY, bot_dir)
    if isinstance(data, dict):
        return data
    return {}


def _role_perms_embed(bot_ref) -> discord.Embed:
    bd = bot_ref._bot_dir
    perms_data = _get_role_perms_cfg(bd)
    lines = []
    for cat_key, cat_info in PERMS_CATEGORIES.items():
        if cat_key == "interactive":
            continue
        perms_list = perms_data.get(cat_key, [])
        count = len(perms_list)
        badge = f"✅ {count} صلاحية" if count else "⬜ لم تُحدَّد"
        lines.append(f"**{cat_info['label']}** — {badge}")
    return _embed(
        "🔐  صلاحيات الرتب",
        "اختر الفئة من القائمة لتحديد صلاحياتها في ديسكورد.\n"
        "كل ضغطة على المنيو تصفّر الاختيارات — اختر ثم اضغط **✅ انهاء** لحفظ الصلاحيات.\n"
        f"{_sep()}"
        + "\n".join(lines)
        + f"{_sep()}"
        "✅ البوت سيُطبّق هذه الصلاحيات مباشرةً على الرتب في ديسكورد — بشرط أن رتبة البوت أعلى منها في الترتيب.",
        C.PURPLE,
        footer="System Bot  •  🔐 صلاحيات الرتب  •  v6.0"
    )


class RolePermsView(View):
    """منيو اختيار الفئة ثم صلاحياتها"""
    def __init__(self, bot_ref, caller_id: int = None):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.caller_id = int(caller_id) if caller_id else None
        cat_options = []
        for cat_key, info in PERMS_CATEGORIES.items():
            if cat_key == "interactive":
                continue
            emoji_str = emojis_config.ROLE_CATEGORIES_EMOJIS.get(info.get("emoji_key", cat_key), "📋")
            try:
                emoji = discord.PartialEmoji.from_str(emoji_str)
            except:
                emoji = emoji_str
            cat_options.append(
                discord.SelectOption(label=info["label"], value=cat_key,
                                     description=f"تحديد صلاحيات {info['label']}", emoji=emoji)
            )
        cat_sel = discord.ui.Select(
            placeholder="اختر فئة الرتبة لتحديد صلاحياتها...",
            options=cat_options, custom_id="rp_cat_sel_v6", row=0)
        cat_sel.callback = self._on_cat_select
        self.add_item(cat_sel)

    async def _on_cat_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        cat_key = interaction.data["values"][0]
        cat_label = PERMS_CATEGORIES[cat_key]["label"]
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **صلاحيات فئة {cat_label}**\nاختر الرتبة:",
            view=PermsSelectView(self.bot, cat_key, self.caller_id),
            embeds=[])

    @discord.ui.button(label="◀  رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="rp_back_v6", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **الخطوة 1: إعداد الرتب**\nاختر فئة الرتبة من القائمة:",
            view=Step1RolesView(self.bot, self.caller_id),
            embeds=[])


def _perms_select_embed(cat_key: str, cat_label: str) -> discord.Embed:
    return _embed(
        f"🔐  صلاحيات {cat_label}",
        f"اختر الصلاحيات التي تريد منحها لفئة **{cat_label}**.\n\n"
        "• كل ضغطة على المنيو **تصفّر** الاختيار السابق\n"
        "• اختر ما تريد ثم اضغط **✅ انهاء** لحفظ وللرجوع للقائمة الرئيسية",
        C.PURPLE,
        footer="System Bot  •  🔐 صلاحيات الرتب  •  v6.0"
    )


class PermsSelectView(View):
    """منيو اختيار الصلاحيات لفئة معينة — كل ضغطة تصفّر"""
    def __init__(self, bot_ref, cat_key: str, caller_id: int = None):
        super().__init__(timeout=None)
        self.bot     = bot_ref
        self.cat_key = cat_key
        self.caller_id = int(caller_id) if caller_id else None
        self._selected_perms: list[str] = []

        perm_options = []
        emoji_str = emojis_config.GENERIC_EMOJIS.get("settings", "⚙️")
        try:
            emoji = discord.PartialEmoji.from_str(emoji_str)
        except:
            emoji = emoji_str
        for perm_name, label in DISCORD_PERMISSIONS:
            perm_options.append(discord.SelectOption(label=label[:100], value=perm_name, emoji=emoji))
        # ديسكورد يسمح بـ 25 خيار كحد أقصى في كل Select — نقسّم على منيوين
        sel1 = discord.ui.Select(
            placeholder="📋  الصلاحيات (١ — ٢٥)...",
            options=perm_options[:25],
            min_values=0, max_values=25,
            custom_id="ps_sel1_v6", row=0)
        sel1.callback = self._on_sel1

        sel2 = discord.ui.Select(
            placeholder="📋  الصلاحيات (٢٦ — آخر)...",
            options=perm_options[25:] if len(perm_options) > 25 else [
                discord.SelectOption(label="—", value="_none")],
            min_values=0, max_values=min(25, max(1, len(perm_options) - 25)),
            custom_id="ps_sel2_v6", row=1)
        sel2.callback = self._on_sel2

        self.add_item(sel1)
        self.add_item(sel2)

    async def _on_sel1(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        # تصفير الجزء الأول وإعادة تعيينه
        vals = [v for v in interaction.data["values"] if v != "_none"]
        # احتفظ بالجزء الثاني إذا كان محدد مسبقاً
        second_part = [p for p in self._selected_perms
                       if p not in [x for x, _ in DISCORD_PERMISSIONS[:25]]]
        self._selected_perms = vals + second_part
        await interaction.edit_original_response(
            embed=_perms_select_embed(self.cat_key, PERMS_CATEGORIES[self.cat_key]["label"]),
            view=self)

    async def _on_sel2(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        vals = [v for v in interaction.data["values"] if v != "_none"]
        first_part = [p for p in self._selected_perms
                      if p in [x for x, _ in DISCORD_PERMISSIONS[:25]]]
        self._selected_perms = first_part + vals
        await interaction.edit_original_response(
            embed=_perms_select_embed(self.cat_key, PERMS_CATEGORIES[self.cat_key]["label"]),
            view=self)

    @discord.ui.button(label="✅  انهاء", style=discord.ButtonStyle.success,
                       custom_id="ps_done_v6", row=2)
    async def done_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        bd = self.bot._bot_dir
        perms_data = _get_role_perms_cfg(bd)
        perms_data[self.cat_key] = self._selected_perms
        set_cfg(PERMS_CFG_KEY, perms_data, bd)
        cat_label = PERMS_CATEGORIES[self.cat_key]["label"]
        count = len(self._selected_perms)

        # ── تطبيق الصلاحيات مباشرة على رتب ديسكورد ──────────────────────────
        guild = interaction.guild
        bot_top = _top_role_pos(guild.me) if guild.me else 0
        role_ids = get_role_list(self.cat_key, bd)
        applied, skipped = [], []
        perm_kwargs = {p: True for p in self._selected_perms if p != "_none"}
        for rid in role_ids:
            role = guild.get_role(rid)
            if not role:
                skipped.append(str(rid))
                continue
            if role.position >= bot_top:
                skipped.append(role.name)
                continue
            try:
                await role.edit(permissions=discord.Permissions(**perm_kwargs),
                                reason=f"System Bot — صلاحيات {cat_label}")
                applied.append(role.name)
            except Exception:
                skipped.append(role.name)

        await interaction.edit_original_response(
            embed=_role_perms_embed(self.bot),
            view=RolePermsView(self.bot, self.caller_id))

        result_lines = []
        if applied:
            result_lines.append(f"✅ طُبِّقت على: {', '.join(applied)}")
        if skipped:
            result_lines.append(f"⚠️ تخطّى (رتبة البوت أدناها أو غير موجودة): {', '.join(skipped)}")

        await interaction.followup.send(
            embed=_embed("✅ تم الحفظ والتطبيق",
                         f"تم حفظ **{count}** صلاحية لفئة **{cat_label}**.\n"
                         + "\n".join(result_lines), C.SUCCESS),
            ephemeral=True)


FEATURES = {
    "feature_welcome":       ("cinematic_welcome", "نظام الترحب",    True),
    "feature_log":           ("smart_log", "نظام اللوق",     True),
    "feature_sanctions":     ("sanctions_system", "نظام العقوبات",        True),
    "feature_auto_mod":      ("protection_system", "نظام الحماية",         True),
    "feature_auto_role":     ("auto_role", "الرول التلقائي",       True),
    "feature_self_roles":    ("interactive_roles", "الرتب التفاعلية",      True),
    "feature_reaction_room": ("room_reaction", "نظام الرياكشن",     True),
    "feature_auto_reply":    ("auto_reply", "الرد التلقائي",    True),
    "feature_separators":    ("separators", "نظام الفواصل",   True),
}

def _step2_features_embed(bot_ref) -> discord.Embed:
    bd = bot_ref._bot_dir
    lines = []
    for fkey, (emoji_key, name, _) in FEATURES.items():
        enabled = bool(cfg(fkey, bd))
        # Get emoji from config or use fallback
        feature_emoji_str = emojis_config.FEATURE_EMOJIS.get(emoji_key, "📋")
        status_emoji_str = emojis_config.STATUS_EMOJIS["enabled"] if enabled else emojis_config.STATUS_EMOJIS["disabled"]
        
        # Use unicode fallbacks for embed text to avoid raw emoji syntax
        feature_emoji_unicode = "📋"  # Use simple unicode for embed
        status_emoji_unicode = "✅" if enabled else "❌"  # Use unicode for embed text
        
        badge = f"{status_emoji_unicode} مُفعَّلة" if enabled else f"{status_emoji_unicode} معطّلة"
        lines.append(f"{feature_emoji_unicode}  **{name}** — {badge}")
    return _embed(
        "⚙️  الخطوة 2 من 3  —  تفعيل الميزات",
        "اختر الميزة من القائمة لتفعيلها أو تعطيلها.\n"
        f"{_sep()}"
        + "\n".join(lines)
        + f"{_sep()}"
        "بعد الانتهاء اضغط **⏩ التالي** لإعداد التفاصيل.",
        C.NAVY,
        footer="System Bot  •  الخطوة 2 من 3  •  Features"
    )


class Step2FeaturesView(View):
    def __init__(self, bot_ref, caller_id: int = None):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.caller_id = int(caller_id) if caller_id else None
        
        bd = bot_ref._bot_dir
        options = []
        for fkey, (emoji_key, name, _) in FEATURES.items():
            enabled = bool(cfg(fkey, bd))
            # Get emojis from config
            feature_emoji_str = emojis_config.FEATURE_EMOJIS.get(emoji_key, "📋")
            
            # Parse custom feature emoji properly for native icon slot
            try:
                feature_emoji = discord.PartialEmoji.from_str(feature_emoji_str)
            except:
                feature_emoji = feature_emoji_str
            
            # Use plain text for status - NO custom emojis in label
            status_text = "[مفعل]" if enabled else "[معطل]"
            clean_label = f"{name} • {status_text}"
            
            options.append(
                discord.SelectOption(
                    label=clean_label,
                    value=fkey,
                    description=f"تفعيل أو تعطيل {name}",
                    emoji=feature_emoji
                )
            )
        
        sel = discord.ui.Select(
            placeholder="اختر الميزة لتفعيلها أو تعطيلها...",
            options=options, custom_id="s2_feat_sel_v5", row=0)
        sel.callback = self._on_toggle
        self.add_item(sel)
        
        # Add navigation buttons with unique custom_ids
        next_btn = discord.ui.Button(label="التالي", emoji=emojis_config.NAV_EMOJIS['next'], style=discord.ButtonStyle.success,
                                      custom_id="step2_next_btn_unique", row=1)
        next_btn.callback = self._next_btn_wrapper
        self.add_item(next_btn)
        
        back_btn = discord.ui.Button(label="رجوع", emoji=emojis_config.NAV_EMOJIS['back'], style=discord.ButtonStyle.secondary,
                                     custom_id="step2_back_btn_unique", row=1)
        back_btn.callback = self._back_btn_wrapper
        self.add_item(back_btn)
    
    async def _next_btn_wrapper(self, interaction: discord.Interaction):
        await self.next_btn(interaction)
    
    async def _back_btn_wrapper(self, interaction: discord.Interaction):
        await self.back_btn(interaction)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the caller to interact with this view"""
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "عفواً، هذه الواجهة مخصصة للشخص الذي استدعى الأمر فقط.",
                ephemeral=True
            )
            return False
        return True

    async def _on_toggle(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        fkey    = interaction.data["values"][0]
        current = bool(cfg(fkey, self.bot._bot_dir))
        new_state = not current
        
        # Conflict detection: Reaction Room vs Auto-Role
        if fkey == "feature_reaction_room" and new_state:
            auto_role_enabled = bool(cfg("feature_auto_role", self.bot._bot_dir))
            if auto_role_enabled:
                set_cfg("feature_auto_role", False, self.bot._bot_dir)
                await interaction.followup.send(
                    embed=_embed("⚠️ تعارض الميزات",
                        "تم تعطيل **الرول التلقائي** تلقائياً لأنه يتعارض مع **نظام الرياكشن**.",
                        C.WARNING),
                    ephemeral=True)
        elif fkey == "feature_auto_role" and new_state:
            reaction_room_enabled = bool(cfg("feature_reaction_room", self.bot._bot_dir))
            if reaction_room_enabled:
                set_cfg("feature_reaction_room", False, self.bot._bot_dir)
                await interaction.followup.send(
                    embed=_embed("⚠️ تعارض الميزات",
                        "تم تعطيل **نظام الرياكشن** تلقائياً لأنه يتعارض مع **الرول التلقائي**.",
                        C.WARNING),
                    ephemeral=True)
        # Auto-reply has no conflicts with other features
        
        set_cfg(fkey, new_state, self.bot._bot_dir)
        emoji_key, name, _ = FEATURES[fkey]
        
        # Rebuild the view with updated status for smooth transition
        bd = self.bot._bot_dir
        options = []
        for fkey_new, (emoji_key_new, name_new, _) in FEATURES.items():
            enabled_new = bool(cfg(fkey_new, bd))
            # Get emojis from config
            feature_emoji_str_new = emojis_config.FEATURE_EMOJIS.get(emoji_key_new, "📋")
            
            # Parse custom feature emoji properly for native icon slot
            try:
                feature_emoji_new = discord.PartialEmoji.from_str(feature_emoji_str_new)
            except:
                feature_emoji_new = feature_emoji_str_new
            
            # Use plain text for status - NO custom emojis in label
            status_text_new = "[مفعل]" if enabled_new else "[معطل]"
            clean_label_new = f"{name_new} • {status_text_new}"
            
            options.append(
                discord.SelectOption(
                    label=clean_label_new,
                    value=fkey_new,
                    description=f"تفعيل أو تعطيل {name_new}",
                    emoji=feature_emoji_new
                )
            )
        
        # Clear all items and rebuild to ensure navigation buttons are preserved
        self.clear_items()
        
        # Re-add the select with updated options
        sel = discord.ui.Select(
            placeholder="اختر الميزة لتفعيلها أو تعطيلها...",
            options=options, custom_id="s2_feat_sel_rebuild", row=0)
        sel.callback = self._on_toggle
        self.add_item(sel)
        
        # Re-add navigation buttons with unique custom_ids
        next_btn = discord.ui.Button(label="التالي", emoji=emojis_config.NAV_EMOJIS['next'], style=discord.ButtonStyle.success,
                                      custom_id="step2_next_btn_rebuild", row=1)
        next_btn.callback = self.next_btn
        self.add_item(next_btn)
        
        back_btn = discord.ui.Button(label="رجوع", emoji=emojis_config.NAV_EMOJIS['back'], style=discord.ButtonStyle.secondary,
                                     custom_id="step2_back_btn_rebuild", row=1)
        back_btn.callback = self.back_btn
        self.add_item(back_btn)
        
        # Edit ONLY the View (no large Embed) to keep chat clean
        await interaction.edit_original_response(view=self)
        
        status_text = "مُفعَّلة" if new_state else "معطّلة"
        await interaction.followup.send(f"✅ {name} الآن {status_text}", ephemeral=True)

    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button = None):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
            view=Step3SettingsView(self.bot, self.caller_id),
            embeds=[])

    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **الخطوة 1: إعداد الرتب**\nاختر فئة الرتبة من القائمة:",
            view=Step1RolesView(self.bot, self.caller_id),
            embeds=[])

# ══════════════════════════════════════════════════════════════════════════════
# SECTION D — الخطوة 3: إعداد التفاصيل (قنوات + رتب الإجازة + auto_role)
# ══════════════════════════════════════════════════════════════════════════════
def _step3_settings_embed(bot_ref, guild: discord.Guild) -> discord.Embed:
    bd  = bot_ref._bot_dir
    def _ch(cid): return guild.get_channel(int(cid)).mention if cid and guild.get_channel(int(cid)) else "⬜ لم تُحدَّد"
    def _role(rid): return guild.get_role(int(rid)).mention if rid and guild.get_role(int(rid)) else "⬜ لم تُحدَّد"

    wch     = cfg("welcome_channel",        bd)
    lch     = cfg("log_channel",            bd)
    slch    = cfg("sanctions_log_channel",  bd)
    ar      = cfg("auto_role",              bd)
    src_ch  = cfg("self_roles_channel",     bd)
    pw_cnt  = len(cfg("prohibited_words", bd) or [])
    lp_cnt  = len((cfg("punishment_config", bd) or {}).get("link_prefixes", []) or [])

    # بناء السطور للميزات المفعّلة فقط
    lines = []
    if bool(cfg("feature_welcome", bd)):
        emoji_unicode = "🎬"
        lines.append(f"**{emoji_unicode} نظام الترحب** ✅ — روم: {_ch(wch)}")
    if bool(cfg("feature_log", bd)):
        emoji_unicode = "📋"
        lines.append(f"**{emoji_unicode} نظام اللوق** ✅ — روم: {_ch(lch)}")
    if bool(cfg("feature_sanctions", bd)):
        emoji_unicode = "⚖️"
        lines.append(f"**{emoji_unicode} لوق العقوبات** ✅ — روم: {_ch(slch)}")
    if bool(cfg("feature_auto_mod", bd)):
        emoji_unicode = "🛡️"
        lines.append(f"**{emoji_unicode} نظام الحماية** ✅ — كلمات: {pw_cnt} | روابط: {lp_cnt}")
    if bool(cfg("feature_auto_role", bd)):
        emoji_unicode = "🤖"
        lines.append(f"**{emoji_unicode} الرول التلقائي** ✅ — رتبة: {_role(ar)}")
    if bool(cfg("feature_self_roles", bd)):
        emoji_unicode = "🎭"
        lines.append(f"**{emoji_unicode} الرتب التفاعلية** ✅ — روم: {_ch(src_ch)}")
    if bool(cfg("feature_reaction_room", bd)):
        emoji_unicode = "🔓"
        lines.append(f"**{emoji_unicode} نظام الرياكشن** ✅ — روم: {_ch(cfg('reaction_room_channel', bd))}")

    body = "\n".join(lines) if lines else "⚠️ لا توجد ميزات مفعّلة — ارجع للخطوة 2 وفعّل الميزات أولاً."

    return _embed(
        "⚙️  الخطوة 3 من 3  —  إعداد التفاصيل",
        f"اختر الميزة من القائمة لضبط إعداداتها التفصيلية.\n"
        f"{_sep()}"
        f"{body}\n"
        f"{_sep()}"
        "اختر ميزة من القائمة أدناه لضبط إعداداتها.",
        C.NAVY,
        footer="System Bot  •  الخطوة 3 من 3  •  Settings"
    )


# ── خيارات الـ Select Menu للخطوة 3 ──────────────────────────────────────────
# mapping ثابت: feature_key → (menu_value, label, description, emoji_key)
# الميزات المرتبطة بـ FEATURES تظهر فقط إذا كانت مفعّلة
# الميزات الثابتة (admin_perms, auto_response) تظهر دائماً
STEP3_FEATURE_MAP = {
    "feature_welcome":    ("welcome",    "نظام الترحب",        "ضبط روم الترحيب + خلفية + رسالة مخصصة", "cinematic_welcome"),
    "feature_log":        ("log",        "نظام اللوق",        "ضبط روم سجل النشاط", "smart_log"),
    "feature_sanctions":  ("sanctions",  "نظام العقوبات",             "ضبط روم سجل العقوبات الإدارية", "sanctions_system"),
    "feature_auto_mod":   ("auto_mod",   "نظام الحماية",  "الكلمات المحظورة + الروابط + العقوبات", "protection_system"),
    "feature_auto_role":  ("auto_role",  "الرول التلقائي",            "ضبط الرول الذي يُعطى لكل عضو جديد", "auto_role"),
    "feature_self_roles": ("self_roles", "الرتب التفاعلية",           "ضبط Self-Roles — رتب يختارها الأعضاء بأزرار", "interactive_roles"),
    "feature_reaction_room": ("reaction_room", "نظام الرياكشن",      "نظام فتح السيرفر بالرياكشن", "room_reaction"),
    "feature_auto_reply":  ("auto_reply",  "الرد التلقائي",           "إضافة وحذف الردود التلقائية", "auto_reply"),
    "feature_separators":  ("separators", "نظام الفواصل",      "إعداد فواصل الصور بين الرسائل", "separators"),
}

# خيارات ثابتة تظهر دائماً بغض النظر عن تفعيل الميزات
STEP3_ALWAYS_OPTIONS = [
    discord.SelectOption(
        label="نظام الأوامر",
        value="admin_perms",
        description="تحديد من يملك صلاحية كل أمر إداري",
        emoji=emojis_config.MAIN_MENU_EMOJIS.get("admin_commands")),
    discord.SelectOption(
        label="نظام المسؤولين",
        value="managers",
        description="إعداد اختصارات الميزات للمسؤولين",
        emoji=emojis_config.MAIN_MENU_EMOJIS.get("managers")),
]

def _build_step3_options(bot_dir) -> list:
    """يبني قائمة خيارات الخطوة 3 بناءً على الميزات المفعّلة فقط"""
    options = []
    for fkey, (val, label, desc, emoji_key) in STEP3_FEATURE_MAP.items():
        if bool(cfg(fkey, bot_dir)):
            emoji = emojis_config.MAIN_MENU_EMOJIS.get(emoji_key)
            options.append(discord.SelectOption(label=label, value=val, description=desc, emoji=emoji))

    # Add always options with their emojis
    for opt in STEP3_ALWAYS_OPTIONS:
        options.append(opt)

    return options


class Step3SettingsView(View):
    """الخطوة 3 — Select Menu ذكي: كل ميزة تفتح واجهتها الخاصة"""
    def __init__(self, bot_ref, caller_id: int = None):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.caller_id = int(caller_id) if caller_id else None
        
        options = _build_step3_options(bot_ref._bot_dir)
        sel = discord.ui.Select(
            placeholder="✦  اختر ميزة لإعدادها...",
            options=options,
            custom_id="s3_main_menu_v6", row=0)
        sel.callback = self._on_feature_select
        self.add_item(sel)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the caller to interact with this view"""
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "عفواً، هذه الواجهة مخصصة للشخص الذي استدعى الأمر فقط.",
                ephemeral=True
            )
            return False
        return True

    async def _on_feature_select(self, interaction: discord.Interaction):
        print(f"DEBUG: Feature selected: {interaction.data.get('values')}")
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        choice = interaction.data["values"][0]

        if choice == "welcome":
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام الترحب**\nحدد الروم والخلفية والرسالة:",
                view=NewWelcomeCardSystem(self.bot),
                embeds=[])
        elif choice == "log":
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام اللوق**\nحدد الروم ووضع اللوق:",
                view=FeatureLogView(self.bot),
                embeds=[])
        elif choice == "sanctions":
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام العقوبات**\nحدد الرولات والرومات والأسباب المطلوب ضبطها:",
                view=SanctionsSetupView(self.bot),
                embeds=[])
        elif choice == "auto_mod":
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام الحماية**\nحدد الكلمات المحظورة والعقوبات:",
                view=FeatureAutoModView(self.bot),
                embeds=[])
        elif choice == "auto_role":
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد الرول التلقائي**\nحدد الرتبة للجديد:",
                view=FeatureAutoRoleView(self.bot),
                embeds=[])
        elif choice == "self_roles":
            # Check Bot Manager permission using dynamic permission function
            if not _has_bot_manager_permission(interaction.user, self.bot._bot_dir):
                return  # Silent denial - no response
            
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد الرتب التفاعلية**\nحدد الروم والرتب:",
                view=FeatureSelfRolesView(self.bot, self.caller_id),
                embeds=[])
        elif choice == "reaction_room":
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **نظام روم الرياكشن**\nاختر الإجراء:",
                view=system_extensions.ReactionRoomMainView(self.bot, self.caller_id),
                embeds=[])
        elif choice == "admin_perms":
            admin_view = FeatureAdminCmdsView(self.bot)
            admin_view.caller_id = self.caller_id
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد الأوامر الإدارية**\nحدد صلاحيات الأوامر:",
                view=admin_view,
                embeds=[])
        elif choice == "auto_reply":
            print("DEBUG: Entering Auto-Response logic")
            try:
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **إعداد الردود التلقائية**\nاختر إجراء للردود التلقائية:",
                    embeds=[],
                    view=FeatureAutoResponseView(self.bot, self.caller_id))
                print("DEBUG: Auto-Response logic executed")
            except Exception as e:
                print(f"DEBUG: SILENT ERROR FOUND in auto_response: {e}")
                import traceback
                traceback.print_exc()
        elif choice == "separators":
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام الفواصل**\nاختر الإجراء:",
                view=system_extensions.SeparatorsMainView(self.bot, self.caller_id),
                embeds=[])
        elif choice == "managers":
            # Check Bot Manager permission using dynamic permission function
            if not _has_bot_manager_permission(interaction.user, self.bot._bot_dir):
                return  # Silent denial - no response
            
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام المسؤولين**\nاختر الإجراء:",
                view=system_extensions.FeatureManagersView(self.bot, self.caller_id),
                embeds=[])

    @discord.ui.button(label="إنهاء 🏁", style=discord.ButtonStyle.success,
                       custom_id="step3_done_btn_unique", row=1)
    async def done_btn(self, interaction: discord.Interaction, button: discord.ui.Button = None):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        reload_config_for(self.bot)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **✅ تم الإعداد بنجاح!**\nالآن البوت جاهز للعمل.\n\nيمكنك استخدام الأوامر الإدارية في الشات.",
            view=HubView(self.bot),
            embeds=[])

    @discord.ui.button(label="رجوع", emoji=emojis_config.NAV_EMOJIS['back'], style=discord.ButtonStyle.secondary,
                       custom_id="step3_back_btn_unique", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **الخطوة 2: تفعيل الميزات**\nاختر الميزة للتفعيل أو التعطيل:",
            view=Step2FeaturesView(self.bot, self.caller_id),
            embeds=[])


# ══════════════════════════════════════════════════════════════════════════════
# SECTION D-2 — واجهات الميزات التفصيلية (كل ميزة = Embed + View + زر رجوع)
# ══════════════════════════════════════════════════════════════════════════════

# ── مساعد رجوع مشترك ─────────────────────────────────────────────────────────
async def _back_to_step3(bot_ref, interaction, caller_id: int = None):
    try:
        return await interaction.edit_original_response(
            content=f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
            view=Step3SettingsView(bot_ref, caller_id or interaction.user.id),
            embeds=[])
    except discord.NotFound:
        # Handle 404 Unknown Webhook errors - interaction expired
        try:
            await interaction.channel.send(
                f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
                view=Step3SettingsView(bot_ref, caller_id or interaction.user.id)
            )
        except Exception as e:
            print(f"[SystemBot] Error in _back_to_step3 fallback: {e}")
    except Exception as e:
        print(f"[SystemBot] Error in _back_to_step3: {e}")


# ────────────────────────────────────────────────────────────────────────────
# 1️⃣  نظام الترحب
# ────────────────────────────────────────────────────────────────────────────
def _feature_welcome_embed(bot_ref, guild: discord.Guild) -> discord.Embed:
    bd  = bot_ref._bot_dir
    wch_id = cfg("welcome_channel", bd)
    wch = guild.get_channel(int(wch_id)).mention if wch_id and guild.get_channel(int(wch_id)) else "لم تُحدَّد"
    enabled = bool(cfg("welcome_enabled", bd))
    bg_url  = cfg("welcome_bg_url", bd) or "—"
    msg_enabled = bool(cfg("welcome_custom_msg_enabled", bd))
    custom_msg = cfg("welcome_custom_msg", bd) or "—"
    
    # Get position info
    av_x = cfg("welcome_avatar_x", bd) or 65
    av_y = cfg("welcome_avatar_y", bd) or 75
    name_x = cfg("welcome_name_x", bd) or 400
    name_y = cfg("welcome_name_y", bd) or 350
    text_x = cfg("welcome_text_x", bd) or 20
    text_y = cfg("welcome_text_y", bd) or 420
    
    # Get status emojis from config
    try:
        status_enabled = emojis_config.STATUS_EMOJIS["enabled"]
        status_disabled = emojis_config.STATUS_EMOJIS["disabled"]
    except Exception:
        status_enabled = "✅"
        status_disabled = "❌"
    
    return _embed(
        "إعداد نظام الترحب",
        f"**الحالة:** {status_enabled if enabled else status_disabled} {'مُفعَّل' if enabled else 'معطّل'}\n"
        f"**روم الترحيب:** {wch}\n"
        f"**رابط الخلفية:** `{bg_url[:60]}`\n"
        f"**الرسالة المخصصة:** {status_enabled if msg_enabled else status_disabled} {'مُفعَّل' if msg_enabled else 'معطّل'}\n"
        f"**نص الرسالة:** `{custom_msg[:80]}`\n"
        f"{_sep()}"
        f"**الإحداثيات:**\n"
        f"صورة العضو: x={av_x}, y={av_y}\n"
        f"اسم العضو: x={name_x}, y={name_y}\n"
        f"النص: x={text_x}, y={text_y}\n"
        f"{_sep()}"
        "استخدم القائمة لضبط كل إعداد.",
        C.PURPLE,
        footer="System Bot  •  إعداد الترحيب  •  v7.0"
    )


class NewWelcomeCardSystem(View):
    """واجهة نظام الترحب - Select Menu متسلسل بدون Embeds"""
    def __init__(self, bot_ref):
        super().__init__(timeout=None)
        self.bot = bot_ref
        bd = bot_ref._bot_dir

        # Get emojis from config
        try:
            emoji_channel = emojis_config.WELCOME_EMOJIS["channel"]
            emoji_background = emojis_config.WELCOME_EMOJIS["background"]
            emoji_avatar_edit = emojis_config.WELCOME_EMOJIS["avatar_edit"]
            emoji_preview = emojis_config.WELCOME_EMOJIS["preview"]
        except Exception:
            emoji_channel = None
            emoji_background = None
            emoji_avatar_edit = None
            emoji_preview = None

        # Main select menu - removed enable/disable options
        options = [
            discord.SelectOption(label="اختيار قناة الترحيب", value="channel",
                               description="اختر القناة التي تُرسل فيها الترحيبات", emoji=emoji_channel),
            discord.SelectOption(label="تعيين خلفية الترحيب", value="background",
                               description="رفع صورة كخلفية للترحيب", emoji=emoji_background),
            discord.SelectOption(label="تعديل الأفاتار", value="avatar_edit",
                               description="تحديد موقع وحجم الأفاتار", emoji=emoji_avatar_edit),
            discord.SelectOption(label="معاينة (Preview)", value="preview",
                               description="توليد صورة تجريبية للترحيب", emoji=emoji_preview),
        ]

        sel = discord.ui.Select(
            placeholder="اختر إعداد نظام الترحب...",
            options=options,
            custom_id="fw_main_sel_v8",
            row=0
        )
        sel.callback = self._on_main_select
        self.add_item(sel)

    async def _on_main_select(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        
        choice = interaction.data["values"][0]

        if choice == "channel":
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **اختيار قناة الترحيب**\nاختر القناة من القائمة أدناه:",
                view=CustomChannelSelector(self.bot)
            )
        elif choice == "background":
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **تعيين خلفية الترحيب**\nأرسل صورة كخلفية للترحيب في الشات...",
                view=NewWelcomeCardSystem(self.bot)
            )
            await interaction.followup.send("بانتظار الصورة...", ephemeral=True)
            await self._wait_for_image_upload(interaction)
        elif choice == "avatar_edit":
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **تعديل الأفاتار / النظام**\n\n🔗 **رابط المحرر:** https://moh823728.github.io/profil/\n\n📋 **التعليمات:\n1. افتح الرابط أعلاه في متصفحك\n2. قم بتخصيص الأفاتار والاسم والرسالة\n3. اضغط على \"نسخ الإعدادات والإحداثيات\"\n4. ارجع هنا واضغط **[ التالي ]** للصق الإعدادات",
                view=WelcomeEditorNavigationView(self.bot)
            )
        elif choice == "preview":
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **جاري توليد معاينة...**",
                view=NewWelcomeCardSystem(self.bot)
            )
            await interaction.followup.send("جاري التوليد...", ephemeral=True)
            await self._generate_preview(interaction)

    async def _wait_for_image_upload(self, interaction: discord.Interaction):
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id and m.attachments
        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            attachment = msg.attachments[0]
            if not attachment.content_type.startswith("image/"):
                await interaction.followup.send("❌ يجب إرسال صورة فقط.", ephemeral=True)
                await msg.delete()
                return
            
            # Save to DM storage (unified system)
            bg_url = attachment.url
            guild_id = interaction.guild.id
            bd = self.bot._bot_dir
            saved = await v2_save_background_image(guild_id, bg_url, bd, self.bot)
            
            if saved:
                _set_guild_cfg("welcome_enabled", guild_id, True, bd)
                reload_config_for(self.bot)
                
                # Send immediate DM echo to user
                try:
                    dm_channel = await interaction.user.create_dm()
                    image_bytes = await _fetch_bytes(attachment.url)
                    if image_bytes:
                        file = discord.File(io.BytesIO(image_bytes), filename="welcome_bg_saved.png")
                        await dm_channel.send(
                            "✅ تم استلام خلفية الترحيب بنجاح! هذه الصورة هي النسخة المعتمدة حالياً لسيرفرك وسيتم التعديل عليها مباشرة.",
                            file=file
                        )
                except Exception as dm_ex:
                    print(f"[Old Welcome] Failed to send DM echo: {dm_ex}")
                    # Fallback: send to log channel if available
                    log_ch_id = cfg("log_channel", bd)
                    if log_ch_id:
                        try:
                            log_ch = interaction.guild.get_channel(log_ch_id)
                            if log_ch:
                                image_bytes = await _fetch_bytes(attachment.url)
                                if image_bytes:
                                    file = discord.File(io.BytesIO(image_bytes), filename="welcome_bg_saved.png")
                                    await log_ch.send(
                                        f"✅ تم استلام خلفية الترحيب بنجاح لسيرفر {interaction.guild.name} من {interaction.user.mention}! هذه الصورة هي النسخة المعتمدة حالياً وسيتم التعديل عليها مباشرة.",
                                        file=file
                                    )
                        except Exception as log_ex:
                            print(f"[Old Welcome] Failed to send to log channel: {log_ex}")
                
                # Clean user message
                await msg.delete()
                
                # Update response immediately without embed
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                    view=NewWelcomeCardSystem(self.bot)
                )
                await interaction.followup.send("تم حفظ الصورة بنجاح!", ephemeral=True)
            else:
                await interaction.followup.send("❌ فشل حفظ الصورة.", ephemeral=True)
                await msg.delete()
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ انتهت المهلة", ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                view=NewWelcomeCardSystem(self.bot)
            )
        except Exception as ex:
            await interaction.followup.send(f"❌ خطأ: {ex}", ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                view=NewWelcomeCardSystem(self.bot)
            )



    async def _generate_preview(self, interaction: discord.Interaction):
        try:
            bd = self.bot._bot_dir
            guild = interaction.guild
            guild_id = guild.id
            
            # Check if guild has background URL in server_images.json
            bg_url = _get_guild_image_url(guild_id)
            if not bg_url:
                print(f"[Old Welcome Preview] Error: No welcome_bg_url found in server_images.json for guild {guild_id}")
                import traceback
                traceback.print_exc()
                await interaction.followup.send("⚠️ يوجد خطأ: لم يتم رفع صورة خلفية لهذا السيرفر بعد، يرجى رفع صورة أولاً.", ephemeral=True)
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                    view=NewWelcomeCardSystem(self.bot)
                )
                return
            
            # Fetch background from unified storage - NO FALLBACK
            bg_bytes = await v2_fetch_background_image(guild_id, bd, self.bot)
            
            if not bg_bytes:
                print(f"[Old Welcome Preview] Error: Failed to fetch background bytes for guild {guild_id}")
                import traceback
                traceback.print_exc()
                await interaction.followup.send("⚠️ يوجد خطأ: تعذر تحميل صورة الخلفية. راجع الـ Terminal للتفاصيل.", ephemeral=True)
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                    view=NewWelcomeCardSystem(self.bot)
                )
                return
            
            # Get avatar URL
            avatar_url = guild.me.display_avatar.with_format("png").url
            
            # Get custom coordinates and size from config
            avatar_x = _guild_cfg("welcome_avatar_x", guild_id, bd)
            avatar_y = _guild_cfg("welcome_avatar_y", guild_id, bd)
            avatar_size = _guild_cfg("welcome_avatar_size", guild_id, bd) or 200
            
            # Generate welcome card with avatar only and custom coordinates
            img_bytes = await v2_generate_welcome_card(avatar_url, bg_bytes, avatar_size, avatar_x, avatar_y)
            
            if not img_bytes:
                print(f"[Old Welcome Preview] Error: Failed to generate welcome card for guild {guild_id}")
                import traceback
                traceback.print_exc()
                await interaction.followup.send("⚠️ يوجد خطأ: تعذر توليد بطاقة الترحيب. راجع الـ Terminal للتفاصيل.", ephemeral=True)
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                    view=NewWelcomeCardSystem(self.bot)
                )
                return
            
            # Send the preview image
            file = discord.File(io.BytesIO(img_bytes), filename="welcome_preview.png")
            await interaction.followup.send(file=file, ephemeral=True)
            
            # Reset the main view
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                view=NewWelcomeCardSystem(self.bot)
            )
        except Exception as ex:
            print(f"[NewWelcomeCardSystem] Preview error: {ex}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ خطأ في توليد المعاينة: {ex}", ephemeral=True)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                view=NewWelcomeCardSystem(self.bot)
            )

    @discord.ui.button(label="رجوع للقائمة", style=discord.ButtonStyle.secondary,
                       custom_id="fw_back_v8", row=2)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
            view=Step3SettingsView(self.bot),
            embeds=[])



class CustomChannelSelector(View):
    """قائمة اختيار قناة الترحيب"""
    def __init__(self, bot_ref):
        super().__init__(timeout=None)
        self.bot = bot_ref
        
        ch_sel = discord.ui.ChannelSelect(
            placeholder="اختر روم الترحيب...",
            custom_id="fw_ch_sel_v9",
            row=0,
            channel_types=[discord.ChannelType.text]
        )
        ch_sel.callback = self._on_ch_select
        self.add_item(ch_sel)
    
    async def _on_ch_select(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        ch_id = int(interaction.data["values"][0])
        guild_id = interaction.guild.id
        bd = self.bot._bot_dir
        _set_guild_cfg("welcome_channel", guild_id, ch_id, bd)
        _set_guild_cfg("welcome_enabled", guild_id, True, bd)
        reload_config_for(self.bot)
        ch = interaction.guild.get_channel(ch_id)
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **إعداد نظام الترحب**",
            view=NewWelcomeCardSystem(self.bot)
        )
        await interaction.followup.send(
            f"تم حفظ القناة: {ch.mention if ch else ch_id}\nتم تفعيل نظام الترحب تلقائياً",
            ephemeral=True
        )
    
    @discord.ui.button(label="رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="fw_ch_back_v9", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **إعداد نظام الترحب**",
            view=NewWelcomeCardSystem(self.bot)
        )


class CoordinateEditorModal(Modal, title="ضبط الإحداثيات"):
    """Modal لضبط إحداثيات عناصر صورة الترحيب"""
    def __init__(self, bot_ref, guild_id: int):
        super().__init__()
        self.bot = bot_ref
        self.guild_id = guild_id
        bd = bot_ref._bot_dir
        
        self.avatar_coords = TextInput(
            label="Avatar (X, Y) - اترك فارغاً للوسط",
            placeholder=f"{_guild_cfg('welcome_avatar_x', guild_id, bd) or ''}, {_guild_cfg('welcome_avatar_y', guild_id, bd) or ''}",
            default=f"{_guild_cfg('welcome_avatar_x', guild_id, bd) or ''}, {_guild_cfg('welcome_avatar_y', guild_id, bd) or ''}",
            required=False,
            max_length=20,
            row=0
        )
        self.avatar_size = TextInput(
            label="Avatar Size (Pixels)",
            placeholder=f"{_guild_cfg('welcome_avatar_size', guild_id, bd) or 200}",
            default=f"{_guild_cfg('welcome_avatar_size', guild_id, bd) or 200}",
            required=True,
            max_length=5,
            row=1
        )
        
        self.add_item(self.avatar_coords)
        self.add_item(self.avatar_size)
    
    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        
        try:
            bd = self.bot._bot_dir
            guild_id = self.guild_id
            
            # Parse avatar coordinates (optional)
            av_x = None
            av_y = None
            if self.avatar_coords.value.strip():
                av_parts = [x.strip() for x in self.avatar_coords.value.split(',')]
                if len(av_parts) == 2:
                    av_x = int(av_parts[0]) if av_parts[0] else None
                    av_y = int(av_parts[1]) if av_parts[1] else None
            
            # Parse avatar size (required)
            avatar_size = int(self.avatar_size.value) if self.avatar_size.value else 200
            
            _set_guild_cfg("welcome_avatar_x", guild_id, av_x, bd)
            _set_guild_cfg("welcome_avatar_y", guild_id, av_y, bd)
            _set_guild_cfg("welcome_avatar_size", guild_id, avatar_size, bd)
            reload_config_for(self.bot)
            
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **إعداد نظام الترحب**",
                view=NewWelcomeCardSystem(self.bot)
            )
            await interaction.followup.send("تم تحديث الإحداثيات بنجاح!", ephemeral=True)
        except ValueError as ve:
            await interaction.response.send_message(f"❌ تنسيق غير صحيح: {ve}", ephemeral=True)
        except Exception as ex:
            await interaction.response.send_message(f"❌ خطأ: {ex}", ephemeral=True)


# ────────────────────────────────────────────────────────────────────────────
# 2️⃣  نظام اللوق 
# ────────────────────────────────────────────────────────────────────────────
def _feature_log_embed(bot_ref, guild: discord.Guild) -> discord.Embed:
    bd      = bot_ref._bot_dir
    enabled = bool(cfg("feature_log", bd))
    mode    = cfg("log_mode", bd) or "unified"

    def _ch(cid):
        ch = guild.get_channel(int(cid)) if cid and int(cid) else None
        return ch.mention if ch else "لم تُحدَّد"

    if mode == "unified":
        lch_id = cfg("log_channel", bd)
        details = f"**روم اللوق الموحد:** {_ch(lch_id)}"
    else:
        cat_id = cfg("log_category_id", bd)
        cat    = guild.get_channel(int(cat_id)) if cat_id and int(cat_id) else None
        details = (
            f"**الكاتيجوري:** {'`' + cat.name + '`' if cat else 'لم تُحدَّد'}\n"
            f"**لوق الصوت:** {_ch(cfg('log_voice_channel', bd))}\n"
            f"**لوق الشات:** {_ch(cfg('log_chat_channel', bd))}\n"
            f"**لوق الإدارة:** {_ch(cfg('log_admin_channel', bd))}\n"
            f"**لوق الدخول/الخروج:** {_ch(cfg('log_join_leave_ch', bd))}"
        )

    mode_badge = "موحد (All-in-One)" if mode == "unified" else "مخصص (Detailed)"
    return _embed(
        "إعداد نظام اللوق",
        f"**الحالة:** {'مُفعَّل' if enabled else 'معطّل'}\n"
        f"**الوضع الحالي:** {mode_badge}\n"
        f"{_sep()}"
        f"{details}\n"
        f"{_sep()}"
        "اختر الوضع ثم حدد القنوات.",
        C.INFO,
        footer="System Bot  •  نظام اللوق  •  v7.0"
    )


class FeatureLogView(View):
    """واجهة نظام اللوق — يدعم الوضع الموحد والمخصص"""
    def __init__(self, bot_ref, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.is_shortcut = is_shortcut

        # Get emojis from config
        try:
            emoji_unified = emojis_config.LOGS_MENU_EMOJIS["unified"]
            emoji_custom = emojis_config.LOGS_MENU_EMOJIS["custom"]
        except Exception:
            emoji_unified = None
            emoji_custom = None

        # Mode selection menu
        options = [
            discord.SelectOption(label="الوضع الموحد", value="unified",
                               description="جميع اللوقات في روم واحد", emoji=emoji_unified),
            discord.SelectOption(label="الوضع المخصص", value="custom",
                               description="روم مخصص لكل نوع لوق", emoji=emoji_custom),
        ]
        sel = discord.ui.Select(
            placeholder="اختر وضع اللوق...",
            options=options,
            custom_id="log_mode_sel",
            row=0
        )
        sel.callback = self._on_mode_select
        self.add_item(sel)

        # Back button - only add if not a shortcut
        if not self.is_shortcut:
            back_btn = discord.ui.Button(label="رجوع للقائمة", emoji=emojis_config.NAV_EMOJIS['back'],
                                         style=discord.ButtonStyle.secondary, custom_id="log_back", row=1)
            back_btn.callback = self.back_btn
            self.add_item(back_btn)

    async def _on_mode_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔", ephemeral=True)

        choice = interaction.data["values"][0]

        if choice == "unified":
            set_cfg("log_mode", "unified", self.bot._bot_dir)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام اللوق - الوضع الموحد**\nاختر روم اللوق الموحد:",
                view=LogUnifiedChView(self.bot),
                embeds=[])
            await interaction.followup.send("✅ تم تفعيل الوضع الموحد", ephemeral=True)
        elif choice == "custom":
            set_cfg("log_mode", "detailed", self.bot._bot_dir)
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام اللوق - الوضع المخصص**\nاختر نوع اللوق لتحديد قناته:",
                view=LogDetailedTypesView(self.bot),
                embeds=[])
            await interaction.followup.send("✅ تم تفعيل الوضع المخصص", ephemeral=True)

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        try:
            # Defer immediately to prevent timeout
            await interaction.response.defer()
            
            # If this is a shortcut, don't go back to step 3 - just close the view
            if self.is_shortcut:
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **تم إغلاق لوحة التحكم**",
                    view=None,
                    embeds=[]
                )
                return
            
            await _back_to_step3(self.bot, interaction)
        except discord.NotFound:
            # Handle 404 Unknown Webhook errors - interaction expired
            print(f"[SystemBot] Interaction expired in FeatureLogView back button")
        except Exception as e:
            print(f"[SystemBot] Error in FeatureLogView back button: {e}")


class LogUnifiedChView(View):
    """اختيار روم اللوق الموحد"""
    def __init__(self, bot_ref):
        super().__init__(timeout=None)
        self.bot = bot_ref
        ch_sel = discord.ui.ChannelSelect(
            placeholder="📺 اختر روم اللوق الموحد...",
            custom_id="log_unified_ch_sel", row=0,
            channel_types=[discord.ChannelType.text])
        ch_sel.callback = self._on_select
        self.add_item(ch_sel)

    async def _on_select(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔", ephemeral=True)
        ch_id = int(interaction.data["values"][0])
        set_cfg("log_channel", ch_id, self.bot._bot_dir)
        reload_config_for(self.bot)
        ch = interaction.guild.get_channel(ch_id)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **إعداد نظام اللوق**\nحدد الروم ووضع اللوق:",
            view=FeatureLogView(self.bot),
            embeds=[])
        await interaction.followup.send(f"✅ روم اللوق الموحد: {ch.mention if ch else ch_id}", ephemeral=True)

    @discord.ui.button(label="رجوع", emoji=emojis_config.NAV_EMOJIS['back'], style=discord.ButtonStyle.secondary,
                       custom_id="log_unified_back", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **إعداد نظام اللوق**\nحدد الروم ووضع اللوق:",
            view=FeatureLogView(self.bot),
            embeds=[])


class LogDetailedTypesView(View):
    """اختيار نوع اللوق لتحديد قناته في الوضع المخصص"""
    def __init__(self, bot_ref):
        super().__init__(timeout=None)
        self.bot = bot_ref

        # Get emojis from config
        try:
            emoji_voice = emojis_config.LOGS_MENU_EMOJIS["voice"]
            emoji_chat = emojis_config.LOGS_MENU_EMOJIS["chat"]
            emoji_admin = emojis_config.LOGS_MENU_EMOJIS["admin"]
            emoji_join_leave = emojis_config.LOGS_MENU_EMOJIS["join_leave"]
            emoji_sanctions = emojis_config.LOGS_MENU_EMOJIS["sanctions"]
            emoji_details = emojis_config.LOGS_MENU_EMOJIS["details"]
        except Exception:
            emoji_voice = None
            emoji_chat = None
            emoji_admin = None
            emoji_join_leave = None
            emoji_sanctions = None
            emoji_details = None

        options = [
            discord.SelectOption(label="لوق روم الفويس",    value="voice",      description="دخول/خروج الأعضاء من الرومات الصوتية", emoji=emoji_voice),
            discord.SelectOption(label="لوق الشات",          value="chat",       description="حذف/تعديل الرسائل", emoji=emoji_chat),
            discord.SelectOption(label="لوق الإدارة",       value="admin",      description="طرد/باند/كتم/تحذير", emoji=emoji_admin),
            discord.SelectOption(label="لوق الدخول/الخروج", value="join_leave", description="دخول وخروج الأعضاء", emoji=emoji_join_leave),
            discord.SelectOption(label="لوق العقوبات",      value="sanctions",  description="السجن، فك السجن، والعقوبات", emoji=emoji_sanctions),
            discord.SelectOption(label="تفاصيل اللوق",      value="details",    description="عرض رومات اللوق المحددة حالياً", emoji=emoji_details),
        ]
        sel = discord.ui.Select(placeholder="اختر نوع اللوق لتحديد قناته...",
                                options=options, custom_id="log_type_sel", row=0)
        sel.callback = self._on_select
        self.add_item(sel)

    async def _on_select(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)

        t = interaction.data["values"][0]
        
        # معالجة خيار تفاصيل اللوق
        if t == "details":
            guild = interaction.guild
            bd = self.bot._bot_dir
            
            def _ch(cid):
                ch = guild.get_channel(int(cid)) if cid and int(cid) else None
                return ch.mention if ch else "غير محدد"
            
            details_text = f"""---
# تفاصيل رومات اللوق المضبوطة

روم لوق الدخول والخروج: {_ch(cfg('log_join_leave_ch', bd))}
روم لوق الفويس: {_ch(cfg('log_voice_channel', bd))}
روم لوق العقوبات: {_ch(cfg('log_sanctions_channel', bd))}
روم لوق الإدارة: {_ch(cfg('log_admin_channel', bd))}
---"""
            
            await interaction.followup.send(details_text, ephemeral=True)
            return
        
        names = {"voice": "لوق روم الفويس", "chat": "لوق الشات",
                 "admin": "لوق الإدارة", "join_leave": "لوق الدخول/الخروج",
                 "sanctions": "لوق العقوبات"}
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **اختر روم {names.get(t, t)}**\nاختر القناة من القائمة:",
            view=LogDetailedChSelectView(self.bot, t),
            embeds=[])

    @discord.ui.button(label="رجوع", emoji=emojis_config.NAV_EMOJIS['back'], style=discord.ButtonStyle.secondary,
                       custom_id="log_types_back", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **إعداد نظام اللوق**\nحدد الروم ووضع اللوق:",
            view=FeatureLogView(self.bot),
            embeds=[])


class LogDetailedChSelectView(View):
    """ChannelSelect لنوع لوق معين"""
    def __init__(self, bot_ref, log_type: str):
        super().__init__(timeout=None)
        self.bot      = bot_ref
        self.log_type = log_type
        ch_sel = discord.ui.ChannelSelect(
            placeholder=f"📺 اختر روم اللوق...",
            custom_id=f"log_ch_{log_type}", row=0,
            channel_types=[discord.ChannelType.text])
        ch_sel.callback = self._on_select
        self.add_item(ch_sel)

    async def _on_select(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔", ephemeral=True)
        ch_id  = int(interaction.data["values"][0])
        key_map = {
            "voice":      "log_voice_channel",
            "chat":       "log_chat_channel",
            "admin":      "log_admin_channel",
            "join_leave": "log_join_leave_ch",
            "sanctions":  "log_sanctions_channel",
        }
        set_cfg(key_map[self.log_type], ch_id, self.bot._bot_dir)
        reload_config_for(self.bot)
        ch = interaction.guild.get_channel(ch_id)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **إعداد نظام اللوق**\nحدد الروم ووضع اللوق:",
            view=FeatureLogView(self.bot),
            embeds=[])
        names = {"voice": "روم الفويس", "chat": "الشات",
                 "admin": "الإدارة", "join_leave": "الدخول/الخروج",
                 "sanctions": "العقوبات"}
        await interaction.followup.send(
            embed=_embed("✅ تم", f"روم لوق **{names.get(self.log_type)}**: {ch.mention if ch else ch_id}", C.SUCCESS),
            ephemeral=True)

    @discord.ui.button(label="رجوع", emoji=emojis_config.NAV_EMOJIS['back'], style=discord.ButtonStyle.secondary,
                       custom_id="log_ch_back", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content="🗂️ تفاصيل اللوق المخصص\nاختر نوع اللوق لتحديد قناته:",
            view=LogDetailedTypesView(self.bot),
            embeds=[])


class LogCatPickView(View):
    """اختيار كاتيجوري لإنشاء رومات اللوق داخله"""
    def __init__(self, bot_ref):
        super().__init__(timeout=None)
        self.bot = bot_ref

    @discord.ui.button(label="🏗️ إنشاء كاتيجوري جديد + رومات", style=discord.ButtonStyle.success,
                       custom_id="log_cat_new", row=0)
    async def new_cat_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔", ephemeral=True)
        guild  = interaction.guild
        bd     = self.bot._bot_dir
        bot_me = guild.me
        ow     = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            bot_me:             discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        try:
            cat = await guild.create_category("📋 سجلات النظام", overwrites=ow)
            set_cfg("log_category_id", cat.id, bd)
            ch_unified = await guild.create_text_channel("📋・log",        category=cat, overwrites=ow)
            ch_voice   = await guild.create_text_channel("🎙️・log-voice",  category=cat, overwrites=ow)
            ch_chat    = await guild.create_text_channel("💬・log-chat",   category=cat, overwrites=ow)
            ch_admin   = await guild.create_text_channel("⚖️・log-admin",  category=cat, overwrites=ow)
            ch_join    = await guild.create_text_channel("🚪・log-members",category=cat, overwrites=ow)
            set_cfg("log_channel",        ch_unified.id, bd)
            set_cfg("log_voice_channel",  ch_voice.id,   bd)
            set_cfg("log_chat_channel",   ch_chat.id,    bd)
            set_cfg("log_admin_channel",  ch_admin.id,   bd)
            set_cfg("log_join_leave_ch",  ch_join.id,    bd)
            set_cfg("feature_log", True, bd)
            reload_config_for(self.bot)
            await interaction.followup.send(
                embed=_embed("✅ تم إنشاء رومات اللوق",
                             f"الكاتيجوري: **{cat.name}**\n"
                             f"📋 {ch_unified.mention} — موحد\n"
                             f"🎙️ {ch_voice.mention} — صوت\n"
                             f"💬 {ch_chat.mention} — شات\n"
                             f"⚖️ {ch_admin.mention} — إدارة\n"
                             f"🚪 {ch_join.mention} — دخول/خروج", C.SUCCESS),
                ephemeral=True)
            await interaction.edit_original_response(
                embed=_feature_log_embed(self.bot, guild),
                view=FeatureLogView(self.bot))
        except discord.Forbidden:
            await interaction.followup.send("❌ البوت لا يملك صلاحية إنشاء رومات.", ephemeral=True)
        except Exception as ex:
            await interaction.followup.send(f"❌ خطأ: {ex}", ephemeral=True)

    @discord.ui.button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="log_cat_back", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **إعداد نظام اللوق**\nحدد الروم ووضع اللوق:",
            view=FeatureLogView(self.bot),
            embeds=[])


# ────────────────────────────────────────────────────────────────────────────
# 3️⃣  نظام العقوبات (النظام الجديد - نصي بدون Embeds)
# ────────────────────────────────────────────────────────────────────────────

def _get_sanctions_status_text(bot_ref, guild: discord.Guild) -> str:
    """الحصول على نص حالة نظام العقوبات"""
    bd = bot_ref._bot_dir
    mute_id = cfg("mute_role", bd)
    mute_role = guild.get_role(int(mute_id)).mention if mute_id and guild.get_role(int(mute_id)) else "⬜ لم تُحدَّد"
    
    jail_id = cfg("jail_role_id", bd)
    jail_role = guild.get_role(int(jail_id)).mention if jail_id and guild.get_role(int(jail_id)) else "⬜ لم تُحدَّد"
    
    jail_ch_id = cfg("jail_channel_id", bd)
    jail_ch = guild.get_channel(int(jail_ch_id)).mention if jail_ch_id and guild.get_channel(int(jail_ch_id)) else "⬜ لم تُحدَّد"
    
    mute_ch_id = cfg("mute_channel_id", bd)
    mute_ch = guild.get_channel(int(mute_ch_id)).mention if mute_ch_id and guild.get_channel(int(mute_ch_id)) else "⬜ لم تُحدَّد"
    
    jail_title = cfg("jail_custom_title", bd) or "سجن"
    jail_action = cfg("jail_action_name", bd) or "حبس"
    
    # Show presets count
    presets = cfg("sanction_presets", bd) or []
    presets_count = len(presets)
    
    return f"""**إعداد نظام العقوبات**

─────────────────────────────
**رول الكتم:** {mute_role}
**رول السجن:** {jail_role}
**روم السجن:** {jail_ch}
**روم الإسكات:** {mute_ch}
**اسم السجن:** {jail_title}
**اسم الفعل:** {jail_action}
**أسباب العقوبات:** {presets_count} سبب
─────────────────────────────"""

class SanctionsSetupView(View):
    """قائمة إعداد نظام العقوبات الجديدة - نصية بدون Embeds"""
    
    def __init__(self, bot_ref, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.is_shortcut = is_shortcut
        self.current_view = "main"  # main, roles, reasons, channels
        self._update_menu_options()
        
    def _update_menu_options(self):
        """تحديث خيارات القائمة المنسدلة"""
        # مسح العناصر القديمة
        self.clear_items()
        
        # إضافة القائمة المنسدلة الرئيسية
        if self.current_view == "main":
            select = discord.ui.Select(
                placeholder="اختر الإجراء...",
                custom_id="sanctions_main_select"
            )
            select.add_option(
                label="رولات العقوبات",
                value="roles",
                emoji=emojis_config.SANCTIONS_EMOJIS['roles'],
                description="إعداد رول الكتم ورول السجن"
            )
            select.add_option(
                label="تعديل الأسباب",
                value="reasons",
                emoji=emojis_config.SANCTIONS_EMOJIS['reasons'],
                description="إضافة وإزالة وتعديل أسباب العقوبات"
            )
            select.add_option(
                label="رومات العقوبات",
                value="channels",
                emoji=emojis_config.SANCTIONS_EMOJIS['channels'],
                description="إعداد روم السجن وروم الإسكات"
            )
            select.callback = self._on_main_select
            self.add_item(select)
            
            # Add back button to main view - only if not a shortcut
            if not self.is_shortcut:
                back_btn = discord.ui.Button(
                    label="رجوع للقائمة",
                    style=discord.ButtonStyle.secondary,
                    custom_id="sanctions_main_back_btn",
                    row=1
                )
                back_btn.emoji = emojis_config.NAV_EMOJIS['back']
                back_btn.callback = self._on_main_back_button
                self.add_item(back_btn)
            
        elif self.current_view == "roles":
            select = discord.ui.Select(
                placeholder="اختر الرول...",
                custom_id="sanctions_roles_select"
            )
            select.add_option(
                label="رول الكتم",
                value="mute_role",
                emoji=emojis_config.SANCTIONS_EMOJIS['mute_role'],
                description="اختر رول الكتم الصوتي"
            )
            select.add_option(
                label="رول السجن",
                value="jail_role",
                emoji=emojis_config.SANCTIONS_EMOJIS['jail_role'],
                description="اختر رول السجن"
            )
            select.callback = self._on_roles_select
            self.add_item(select)
            
        elif self.current_view == "reasons":
            select = discord.ui.Select(
                placeholder="اختر الإجراء...",
                custom_id="sanctions_reasons_select"
            )
            select.add_option(
                label="إضافة سبب",
                value="add_reason",
                emoji=emojis_config.SANCTIONS_EMOJIS['add_reason'],
                description="إضافة سبب عقوبة جديد"
            )
            select.add_option(
                label="إزالة سبب",
                value="remove_reason",
                emoji=emojis_config.SANCTIONS_EMOJIS['remove_reason'],
                description="حذف سبب موجود"
            )
            select.add_option(
                label="تعديل سبب",
                value="edit_reason",
                emoji=emojis_config.SANCTIONS_EMOJIS['edit_reason'],
                description="تعديل سبب موجود"
            )
            select.callback = self._on_reasons_select
            self.add_item(select)
            
        elif self.current_view == "channels":
            select = discord.ui.Select(
                placeholder="اختر الروم...",
                custom_id="sanctions_channels_select"
            )
            select.add_option(
                label="روم السجن",
                value="jail_channel",
                emoji=emojis_config.SANCTIONS_EMOJIS['jail_channel'],
                description="اختر روم السجن"
            )
            select.add_option(
                label="روم الإسكات",
                value="mute_channel",
                emoji=emojis_config.SANCTIONS_EMOJIS['mute_channel'],
                description="اختر روم الإسكات"
            )
            select.callback = self._on_channels_select
            self.add_item(select)
        
        # Add back button for all subsections
        if self.current_view != "main":
            back_btn = discord.ui.Button(
                label="رجوع للقائمة",
                style=discord.ButtonStyle.secondary,
                custom_id="sanctions_back_btn",
                row=1
            )
            back_btn.emoji = emojis_config.NAV_EMOJIS['back']
            back_btn.callback = self._on_back_button
            self.add_item(back_btn)
    
    async def _on_back_button(self, interaction: discord.Interaction):
        """معالجة زر الرجوع"""
        try:
            # Defer immediately to prevent timeout
            await interaction.response.defer()
            self.current_view = "main"
            self._update_menu_options()
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد نظام العقوبات**\nحدد الرولات والرومات والأسباب المطلوب ضبطها:",
                view=self
            )
        except discord.NotFound:
            # Handle 404 Unknown Webhook errors - interaction expired
            try:
                self.current_view = "main"
                self._update_menu_options()
                await interaction.channel.send(
                    f"{interaction.user.mention} **إعداد نظام العقوبات**\nحدد الرولات والرومات والأسباب المطلوب ضبطها:",
                    view=self
                )
            except Exception as e:
                print(f"[SystemBot] Error in _on_back_button fallback: {e}")
        except Exception as e:
            print(f"[SystemBot] Error in _on_back_button: {e}")
    
    async def _on_main_back_button(self, interaction: discord.Interaction):
        """معالجة زر الرجوع للقائمة الرئيسية"""
        try:
            # Defer immediately to prevent timeout
            await interaction.response.defer()
            
            # If this is a shortcut, don't go back to step 3 - just close the view
            if self.is_shortcut:
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **تم إغلاق لوحة التحكم**",
                    view=None,
                    embeds=[]
                )
                return
            
            # Return to Step 3 Features Setup View
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
                view=Step3SettingsView(self.bot),
                embeds=[]
            )
        except discord.NotFound:
            # Handle 404 Unknown Webhook errors - interaction expired
            try:
                if self.is_shortcut:
                    await interaction.channel.send(
                        f"{interaction.user.mention} **تم إغلاق لوحة التحكم**",
                        view=None
                    )
                else:
                    await interaction.channel.send(
                        f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
                        view=Step3SettingsView(self.bot)
                    )
            except Exception as e:
                print(f"[SystemBot] Error in _on_main_back_button fallback: {e}")
        except Exception as e:
            print(f"[SystemBot] Error in _on_main_back_button: {e}")
    
    async def _on_main_select(self, interaction: discord.Interaction):
        """معالجة اختيار القائمة الرئيسية"""
        value = interaction.data["values"][0]
        
        if value == "roles":
            self.current_view = "roles"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **إعداد رولات العقوبات**\nاختر الرول من القائمة أدناه:",
                view=self
            )
        elif value == "reasons":
            self.current_view = "reasons"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **تعديل الأسباب**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
        elif value == "channels":
            self.current_view = "channels"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **إعداد رومات العقوبات**\nاختر الروم من القائمة أدناه:",
                view=self
            )
    
    async def _on_roles_select(self, interaction: discord.Interaction):
        """معالجة اختيار رولات العقوبات"""
        value = interaction.data["values"][0]
        
        if value == "mute_role":
            await self._select_role(interaction, "mute_role", "رول الكتم")
        elif value == "jail_role":
            await self._select_role(interaction, "jail_role_id", "رول السجن")
    
    async def _on_reasons_select(self, interaction: discord.Interaction):
        """معالجة اختيار إدارة الأسباب"""
        value = interaction.data["values"][0]
        
        if value == "add_reason":
            await self._add_reason(interaction)
        elif value == "remove_reason":
            await self._remove_reason(interaction)
        elif value == "edit_reason":
            await self._edit_reason(interaction)
    
    async def _on_channels_select(self, interaction: discord.Interaction):
        """معالجة اختيار رومات العقوبات"""
        value = interaction.data["values"][0]
        
        if value == "jail_channel":
            await self._select_channel(interaction, "jail_channel_id", "روم السجن")
        elif value == "mute_channel":
            await self._select_channel(interaction, "mute_channel_id", "روم الإسكات")
    
    async def _select_role(self, interaction: discord.Interaction, config_key: str, role_name: str):
        """اختيار رول من قائمة الرولات"""
        guild = interaction.guild
        bd = self.bot._bot_dir
        
        # إنشاء قائمة الرولات
        options = []
        emoji_str = emojis_config.GENERIC_EMOJIS.get("role", "🎭")
        try:
            emoji = discord.PartialEmoji.from_str(emoji_str)
        except:
            emoji = emoji_str
            
        for role in guild.roles:
            if role.is_default() or role.managed:
                continue
            options.append(discord.SelectOption(label=role.name, value=str(role.id), emoji=emoji))
        
        if not options:
            self.current_view = "roles"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **❌ لا توجد رولات متاحة**\nاختر الرول من القائمة أدناه:",
                view=self
            )
            return
        
        # عرض قائمة الرولات في نفس الـ View
        self.clear_items()
        role_select = discord.ui.Select(
            placeholder=f"اختر {role_name}...",
            options=options[:25],
            custom_id=f"role_select_{config_key}"
        )
        
        async def role_callback(interaction: discord.Interaction):
            role_id = int(interaction.data["values"][0])
            set_cfg(config_key, role_id, bd)
            reload_config_for(self.bot)
            
            self.current_view = "roles"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **✅ تم حفظ {role_name} بنجاح**\nاختر الرول من القائمة أدناه:",
                view=self
            )
        
        role_select.callback = role_callback
        self.add_item(role_select)
        
        # Add back button
        back_btn = discord.ui.Button(
            label="رجوع للقائمة",
            style=discord.ButtonStyle.secondary,
            custom_id="role_back_btn",
            row=1
        )
        back_btn.emoji = emojis_config.NAV_EMOJIS['back']
        
        async def back_callback(interaction: discord.Interaction):
            self.current_view = "roles"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **إعداد رولات العقوبات**\nاختر الرول من القائمة أدناه:",
                view=self
            )
        
        back_btn.callback = back_callback
        self.add_item(back_btn)
        
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **اختر {role_name}**\nاختر الرول من القائمة أدناه:",
            view=self
        )
    
    async def _select_channel(self, interaction: discord.Interaction, config_key: str, channel_name: str):
        """اختيار روم من قائمة الرومات"""
        guild = interaction.guild
        bd = self.bot._bot_dir
        
        # إنشاء قائمة الرومات النصية
        options = []
        emoji_str = emojis_config.GENERIC_EMOJIS.get("channel", "📁")
        try:
            emoji = discord.PartialEmoji.from_str(emoji_str)
        except:
            emoji = emoji_str
            
        for channel in guild.text_channels:
            options.append(discord.SelectOption(label=channel.name, value=str(channel.id), emoji=emoji))
        
        if not options:
            self.current_view = "channels"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **❌ لا توجد رومات متاحة**\nاختر الروم من القائمة أدناه:",
                view=self
            )
            return
        
        # عرض قائمة الرومات في نفس الـ View
        self.clear_items()
        channel_select = discord.ui.Select(
            placeholder=f"اختر {channel_name}...",
            options=options[:25],
            custom_id=f"channel_select_{config_key}"
        )
        
        async def channel_callback(interaction: discord.Interaction):
            channel_id = int(interaction.data["values"][0])
            set_cfg(config_key, channel_id, bd)
            reload_config_for(self.bot)
            
            self.current_view = "channels"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **✅ تم حفظ {channel_name} بنجاح**\nاختر الروم من القائمة أدناه:",
                view=self
            )
        
        channel_select.callback = channel_callback
        self.add_item(channel_select)
        
        # Add back button
        back_btn = discord.ui.Button(
            label="رجوع للقائمة",
            style=discord.ButtonStyle.secondary,
            custom_id="channel_back_btn",
            row=1
        )
        back_btn.emoji = emojis_config.NAV_EMOJIS['back']
        
        async def back_callback(interaction: discord.Interaction):
            self.current_view = "channels"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **إعداد رومات العقوبات**\nاختر الروم من القائمة أدناه:",
                view=self
            )
        
        back_btn.callback = back_callback
        self.add_item(back_btn)
        
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **اختر {channel_name}**\nاختر الروم من القائمة أدناه:",
            view=self
        )
    
    async def _add_reason(self, interaction: discord.Interaction):
        """إضافة سبب جديد باستخدام إدخال الشات"""
        # Edit the original message to show the prompt
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **اكتب اسم السبب في الشات**\n(لإلغاء: اكتب `إلغاء`)",
            view=None
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            
            if msg.content.strip().lower() == 'إلغاء':
                await msg.delete()
                self.current_view = "reasons"
                self._update_menu_options()
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **تعديل الأسباب**\nاختر الإجراء من القائمة أدناه:",
                    view=self
                )
                return
            
            reason_name = msg.content.strip()
            await msg.delete()
            
            # طلب المدة - edit the message to show the next prompt
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **اكتب مدة العقوبة في الشات**\n(مثال: 10min أو 2h أو 5d أو 1m)\n(ملاحظة: min=دقائق، h=ساعات، d=أيام، m=أشهر)\n(لإلغاء: اكتب `إلغاء`)",
                view=None
            )
            
            msg2 = await self.bot.wait_for('message', check=check, timeout=60)
            
            if msg2.content.strip().lower() == 'إلغاء':
                await msg2.delete()
                self.current_view = "reasons"
                self._update_menu_options()
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **تعديل الأسباب**\nاختر الإجراء من القائمة أدناه:",
                    view=self
                )
                return
            
            duration = msg2.content.strip()
            await msg2.delete()
            
            # حفظ السبب
            bd = self.bot._bot_dir
            presets = cfg("sanction_presets", bd) or []
            presets.append({"reason": reason_name, "duration": duration})
            set_cfg("sanction_presets", presets, bd)
            reload_config_for(self.bot)
            
            self.current_view = "reasons"
            self._update_menu_options()
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **✅ تم إضافة السبب: {reason_name} ({duration})**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
            
        except asyncio.TimeoutError:
            self.current_view = "reasons"
            self._update_menu_options()
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **❌ انتهى الوقت. تم إلغاء العملية**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
    
    async def _remove_reason(self, interaction: discord.Interaction):
        """إزالة سبب موجود"""
        bd = self.bot._bot_dir
        presets = cfg("sanction_presets", bd) or []
        
        if not presets:
            self.current_view = "reasons"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **❌ لا توجد أسباب لحذفها**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
            return
        
        # إنشاء قائمة الأسباب
        options = []
        for i, preset in enumerate(presets):
            reason = preset.get("reason", "بدون اسم")
            duration = preset.get("duration", "1h")
            options.append(discord.SelectOption(
                label=f"{reason} ({duration})",
                value=str(i)
            ))
        
        # عرض قائمة الأسباب في نفس الـ View
        self.clear_items()
        reason_select = discord.ui.Select(
            placeholder="اختر السبب الذي تريد حذفه...",
            options=options[:25],
            custom_id="remove_reason_select"
        )
        
        async def remove_callback(interaction: discord.Interaction):
            idx = int(interaction.data["values"][0])
            if 0 <= idx < len(presets):
                deleted = presets.pop(idx)
                set_cfg("sanction_presets", presets, bd)
                reload_config_for(self.bot)
                
                self.current_view = "reasons"
                self._update_menu_options()
                await interaction.response.edit_message(
                    content=f"{interaction.user.mention} **✅ تم حذف السبب: {deleted['reason']}**\nاختر الإجراء من القائمة أدناه:",
                    view=self
                )
        
        reason_select.callback = remove_callback
        self.add_item(reason_select)
        
        # Add back button
        back_btn = discord.ui.Button(
            label="رجوع للقائمة",
            style=discord.ButtonStyle.secondary,
            custom_id="remove_reason_back_btn",
            row=1
        )
        back_btn.emoji = emojis_config.NAV_EMOJIS['back']
        
        async def back_callback(interaction: discord.Interaction):
            self.current_view = "reasons"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **تعديل الأسباب**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
        
        back_btn.callback = back_callback
        self.add_item(back_btn)
        
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **اختر السبب للحذف**\nاختر السبب من القائمة أدناه:",
            view=self
        )
    
    async def _edit_reason(self, interaction: discord.Interaction):
        """تعديل سبب موجود"""
        bd = self.bot._bot_dir
        presets = cfg("sanction_presets", bd) or []
        
        if not presets:
            self.current_view = "reasons"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **❌ لا توجد أسباب لتعديلها**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
            return
        
        # إنشاء قائمة الأسباب
        options = []
        for i, preset in enumerate(presets):
            reason = preset.get("reason", "بدون اسم")
            duration = preset.get("duration", "1h")
            options.append(discord.SelectOption(
                label=f"{reason} ({duration})",
                value=str(i)
            ))
        
        # عرض قائمة الأسباب في نفس الـ View
        self.clear_items()
        reason_select = discord.ui.Select(
            placeholder="اختر السبب المراد تعديله...",
            options=options[:25],
            custom_id="edit_reason_select"
        )
        
        async def edit_callback(interaction: discord.Interaction):
            idx = int(interaction.data["values"][0])
            if 0 <= idx < len(presets):
                # Store the current index for later use in the closure
                edit_idx = idx
                
                # عرض خيارات التعديل في نفس الـ View
                self.clear_items()
                edit_options = discord.ui.Select(
                    placeholder="اختر ما تريد تعديله...",
                    options=[
                        discord.SelectOption(
                            label="تعديل اسم السبب",
                            value="edit_name",
                            emoji=emojis_config.SANCTIONS_EMOJIS['edit_name']
                        ),
                        discord.SelectOption(
                            label="تعديل مدة السبب",
                            value="edit_duration",
                            emoji=emojis_config.SANCTIONS_EMOJIS['edit_duration']
                        )
                    ],
                    custom_id="edit_option_select"
                )
                
                async def edit_option_callback(interaction: discord.Interaction):
                    option = interaction.data["values"][0]
                    idx = edit_idx
                    
                    if option == "edit_name":
                        await interaction.response.edit_message(
                            content=f"{interaction.user.mention} {emojis_config.SANCTIONS_EMOJIS['edit_name']} **اكتب الاسم الجديد للسبب**\n(لإلغاء: اكتب `إلغاء`)",
                            view=None
                        )
                        
                        def check(msg):
                            return msg.author == interaction.user and msg.channel == interaction.channel
                        
                        try:
                            msg = await self.bot.wait_for('message', check=check, timeout=60)
                            
                            if msg.content.strip().lower() == 'إلغاء':
                                await msg.delete()
                                self.current_view = "reasons"
                                self._update_menu_options()
                                await interaction.edit_original_response(
                                    content=f"{interaction.user.mention} **تعديل الأسباب**\nاختر الإجراء من القائمة أدناه:",
                                    view=self
                                )
                                return
                            
                            new_name = msg.content.strip()
                            await msg.delete()
                            
                            presets[idx]["reason"] = new_name
                            set_cfg("sanction_presets", presets, bd)
                            reload_config_for(self.bot)
                            
                            self.current_view = "reasons"
                            self._update_menu_options()
                            await interaction.edit_original_response(
                                content=f"{interaction.user.mention} **✅ تم تعديل الاسم إلى: {new_name}**\nاختر الإجراء من القائمة أدناه:",
                                view=self
                            )
                            
                        except asyncio.TimeoutError:
                            self.current_view = "reasons"
                            self._update_menu_options()
                            await interaction.edit_original_response(
                                content=f"{interaction.user.mention} **❌ انتهى الوقت. تم إلغاء العملية**\nاختر الإجراء من القائمة أدناه:",
                                view=self
                            )
                    
                    elif option == "edit_duration":
                        await interaction.response.edit_message(
                            content=f"{interaction.user.mention} {emojis_config.SANCTIONS_EMOJIS['edit_duration']} **اكتب المدة الجديدة**\n(مثال: 10min أو 2h أو 5d أو 1m)\n(ملاحظة: min=دقائق، h=ساعات، d=أيام، m=أشهر)\n(لإلغاء: اكتب `إلغاء`)",
                            view=None
                        )
                        
                        def check(msg):
                            return msg.author == interaction.user and msg.channel == interaction.channel
                        
                        try:
                            msg = await self.bot.wait_for('message', check=check, timeout=60)
                            
                            if msg.content.strip().lower() == 'إلغاء':
                                await msg.delete()
                                self.current_view = "reasons"
                                self._update_menu_options()
                                await interaction.edit_original_response(
                                    content=f"{interaction.user.mention} **تعديل الأسباب**\nاختر الإجراء من القائمة أدناه:",
                                    view=self
                                )
                                return
                            
                            new_duration = msg.content.strip()
                            await msg.delete()
                            
                            presets[idx]["duration"] = new_duration
                            set_cfg("sanction_presets", presets, bd)
                            reload_config_for(self.bot)
                            
                            self.current_view = "reasons"
                            self._update_menu_options()
                            await interaction.edit_original_response(
                                content=f"{interaction.user.mention} **✅ تم تعديل المدة إلى: {new_duration}**\nاختر الإجراء من القائمة أدناه:",
                                view=self
                            )
                            
                        except asyncio.TimeoutError:
                            self.current_view = "reasons"
                            self._update_menu_options()
                            await interaction.edit_original_response(
                                content=f"{interaction.user.mention} **❌ انتهى الوقت. تم إلغاء العملية**\nاختر الإجراء من القائمة أدناه:",
                                view=self
                            )
                
                edit_options.callback = edit_option_callback
                self.add_item(edit_options)
                
                # Add back button
                back_btn = discord.ui.Button(
                    label="رجوع للقائمة",
                    style=discord.ButtonStyle.secondary,
                    custom_id="edit_option_back_btn",
                    row=1
                )
                back_btn.emoji = emojis_config.NAV_EMOJIS['back']
                
                async def back_callback(interaction: discord.Interaction):
                    self.current_view = "reasons"
                    self._update_menu_options()
                    await interaction.response.edit_message(
                        content=f"{interaction.user.mention} **تعديل الأسباب**\nاختر الإجراء من القائمة أدناه:",
                        view=self
                    )
                
                back_btn.callback = back_callback
                self.add_item(back_btn)
                
                await interaction.response.edit_message(
                    content=f"{interaction.user.mention} **اختر نوع التعديل**\nاختر الإجراء من القائمة أدناه:",
                    view=self
                )
        
        reason_select.callback = edit_callback
        self.add_item(reason_select)
        
        # Add back button
        back_btn = discord.ui.Button(
            label="رجوع للقائمة",
            style=discord.ButtonStyle.secondary,
            custom_id="edit_reason_back_btn",
            row=1
        )
        back_btn.emoji = emojis_config.NAV_EMOJIS['back']
        
        async def back_callback(interaction: discord.Interaction):
            self.current_view = "reasons"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **تعديل الأسباب**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
        
        back_btn.callback = back_callback
        self.add_item(back_btn)
        
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **اختر السبب للتعديل**\nاختر السبب من القائمة أدناه:",
            view=self
        )


async def _sync_mute_role_if_needed(bot_ref, guild: discord.Guild):
    """Background task to sync mute role permissions if configured"""
    bd = bot_ref._bot_dir
    mute_id = cfg("mute_role", bd)
    if mute_id:
        mute_role = guild.get_role(int(mute_id))
        if mute_role:
            await _sync_mute_role_permissions(guild, mute_role)
    
    # Also sync jail role permissions if configured
    jail_id = cfg("jail_role_id", bd)
    jail_ch_id = cfg("jail_channel_id", bd)
    if jail_id:
        jail_role = guild.get_role(int(jail_id))
        if jail_role:
            await _sync_jail_role_permissions(guild, jail_role, jail_ch_id)


async def _sync_mute_role_permissions(guild: discord.Guild, mute_role: discord.Role):
    """Sync mute role permissions across ALL channels (Text, Voice, Categories)"""
    bot_me = guild.me
    if not bot_me:
        return
    
    success_count = 0
    fail_count = 0
    
    for channel in guild.channels:
        try:
            # Explicitly create/update channel overwrites for mute role
            await channel.set_permissions(
                mute_role,
                send_messages=False,
                add_reactions=False,
                create_public_threads=False,
                create_private_threads=False,
                send_messages_in_threads=False,
                speak=False,
                stream=False,
                connect=False,
                reason="System Bot: Automatic Mute Role Permissions Sync"
            )
            success_count += 1
            
            # Rate limit handling - small delay between updates
            await asyncio.sleep(0.1)
            
        except discord.Forbidden:
            fail_count += 1
            print(f"[SystemBot] ⚠️ Missing Manage Channels permission for {channel.name}")
        except discord.HTTPException as ex:
            fail_count += 1
            if ex.status == 429:  # Rate limited
                retry_after = ex.retry_after if hasattr(ex, 'retry_after') else 5
                print(f"[SystemBot] ⚠️ Rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
            else:
                print(f"[SystemBot] ⚠️ HTTP error updating {channel.name}: {ex}")
        except Exception as ex:
            fail_count += 1
            print(f"[SystemBot] ⚠️ Error updating {channel.name}: {ex}")
    
    print(f"[SystemBot] ✅ Mute role permissions synced: {success_count} channels updated, {fail_count} failed")


async def _sync_jail_role_permissions(guild: discord.Guild, jail_role: discord.Role, jail_channel_id: int = 0):
    """Sync jail role permissions across ALL channels (Text, Voice, Categories)"""
    bot_me = guild.me
    if not bot_me:
        return
    
    success_count = 0
    fail_count = 0
    
    for channel in guild.channels:
        try:
            # Check if this is the designated jail channel
            is_jail_channel = (channel.id == jail_channel_id)
            
            if is_jail_channel:
                # Grant access to jail channel
                await channel.set_permissions(
                    jail_role,
                    view_channel=True,
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True,
                    add_reactions=True,
                    reason="System Bot: Jail Role - Allow access to jail channel"
                )
            else:
                # Block access to all other channels
                await channel.set_permissions(
                    jail_role,
                    view_channel=False,
                    read_messages=False,
                    send_messages=False,
                    add_reactions=False,
                    create_public_threads=False,
                    create_private_threads=False,
                    send_messages_in_threads=False,
                    speak=False,
                    stream=False,
                    connect=False,
                    reason="System Bot: Jail Role - Block access"
                )
            success_count += 1
            
            # Rate limit handling - small delay between updates
            await asyncio.sleep(0.1)
            
        except discord.Forbidden:
            fail_count += 1
            print(f"[SystemBot] ⚠️ Missing Manage Channels permission for {channel.name}")
        except discord.HTTPException as ex:
            fail_count += 1
            if ex.status == 429:  # Rate limited
                retry_after = ex.retry_after if hasattr(ex, 'retry_after') else 5
                print(f"[SystemBot] ⚠️ Rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
            else:
                print(f"[SystemBot] ⚠️ HTTP error updating {channel.name}: {ex}")
        except Exception as ex:
            fail_count += 1
            print(f"[SystemBot] ⚠️ Error updating {channel.name}: {ex}")
    
    print(f"[SystemBot] ✅ Jail role permissions synced: {success_count} channels updated, {fail_count} failed")


# ────────────────────────────────────────────────────────────────────────────
# 4️⃣  نظام الحماية (Auto-Mod)
# ────────────────────────────────────────────────────────────────────────────
def _get_punishment_config(bot_dir=None) -> dict:
    data = cfg("punishment_config", bot_dir)
    if not isinstance(data, dict):
        data = {}
    base = dict(_DEFAULTS.get("punishment_config", {}))
    base.update(data)
    if not isinstance(base.get("link_prefixes"), list):
        base["link_prefixes"] = []
    if not isinstance(base.get("exempt_role_ids"), list):
        base["exempt_role_ids"] = []
    if not isinstance(base.get("word_penalties"), dict):
        base["word_penalties"] = {}
    base["action"] = _normalize_punishment_action(base.get("action"))
    return base


def _feature_automod_embed(bot_ref, guild: discord.Guild) -> discord.Embed:
    bd      = bot_ref._bot_dir
    enabled = bool(cfg("feature_auto_mod", bd))
    words   = cfg("prohibited_words", bd) or []
    p_cfg   = _get_punishment_config(bd)
    links   = p_cfg.get("link_prefixes", []) or []
    action  = p_cfg.get("action", "timeout")
    duration_raw = p_cfg.get("duration", "") or ""
    dur_secs = _parse_duration_seconds(duration_raw)
    dur_txt = _format_duration(dur_secs) if dur_secs else ("دائم" if action == "ban" else "—")
    reason  = p_cfg.get("reason", "—")
    words_preview = "، ".join(words[:8]) if words else "⬜ لا توجد كلمات"
    links_preview = "، ".join(links[:8]) if links else "⬜ لا توجد روابط"
    return _embed(
        "🛡️  إعداد نظام الحماية (Auto-Mod)",
        f"**الحالة:** {'🟢 مُفعَّل' if enabled else '🔴 معطّل'}\n"
        f"**الكلمات المحظورة:** `{len(words)}`\n"
        f"**روابط محظورة:** `{len(links)}`\n"
        f"**العقوبة الحالية:** {_punishment_label(action)}\n"
        f"**المدة:** {dur_txt}\n"
        f"**السبب:** `{reason[:80]}`\n"
        f"{_sep()}"
        f"**📌 كلمات:** {words_preview}\n"
        f"**🔗 روابط:** {links_preview}\n"
        f"{_sep()}"
        "اختر إعداداً من القائمة أدناه لتعديله.",
        C.GRAPHITE,
        footer="System Bot  •  🛡️ Auto-Mod  •  v7.0"
    )


class FeatureAutoModView(View):
    """نظام الحماية المعاد بناؤه - بدون Modals مع قوائم اختيار شاملة"""
    
    def __init__(self, bot_ref, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.is_shortcut = is_shortcut
        self.current_view = "main"  # main, words_submenu, links_submenu, anti_nuke
        self._update_menu_options()
        
    def _update_menu_options(self):
        """تحديث خيارات القائمة المنسدلة"""
        self.clear_items()
        
        if self.current_view == "main":
            select = discord.ui.Select(
                placeholder="اختر الإجراء...",
                custom_id="protection_main_select"
            )
            select.add_option(
                label="إدارة الكلمات المحظورة",
                value="banned_words",
                emoji=emojis_config.PROTECTION_EMOJIS['banned_words'],
                description="إضافة وإزالة الكلمات المحظورة"
            )
            select.add_option(
                label="حماية الروابط",
                value="anti_links",
                emoji=emojis_config.PROTECTION_EMOJIS['anti_links'],
                description="تفعيل/تعطيل حماية الروابط والرتب المستثناة"
            )
            select.add_option(
                label="نظام مكافحة التخريب",
                value="anti_nuke",
                emoji=emojis_config.PROTECTION_EMOJIS['anti_nuke'],
                description="تعيين العقوبات حسب نوع المخالفة"
            )
            select.callback = self._on_main_select
            self.add_item(select)
            
            # Add back button to main view - only if not a shortcut
            if not self.is_shortcut:
                back_btn = discord.ui.Button(
                    label="رجوع للقائمة",
                    style=discord.ButtonStyle.secondary,
                    custom_id="protection_main_back_btn",
                    row=1
                )
                back_btn.emoji = emojis_config.NAV_EMOJIS['back']
                back_btn.callback = self._on_main_back_button
                self.add_item(back_btn)
            
        elif self.current_view == "words_submenu":
            select = discord.ui.Select(
                placeholder="اختر الإجراء...",
                custom_id="words_submenu_select"
            )
            select.add_option(
                label="إضافة كلمة محظورة",
                value="add_word",
                emoji=emojis_config.PROTECTION_EMOJIS['add_word'],
                description="إضافة كلمة جديدة للقائمة المحظورة"
            )
            select.add_option(
                label="إزالة كلمة محظورة",
                value="remove_word",
                emoji=emojis_config.PROTECTION_EMOJIS['remove_word'],
                description="حذف كلمة من القائمة المحظورة"
            )
            select.callback = self._on_words_submenu_select
            self.add_item(select)
            
            # Add back button
            back_btn = discord.ui.Button(
                label="رجوع للقائمة",
                style=discord.ButtonStyle.secondary,
                custom_id="words_back_btn",
                row=1
            )
            back_btn.emoji = emojis_config.NAV_EMOJIS['back']
            back_btn.callback = self._on_words_back_button
            self.add_item(back_btn)
            
        elif self.current_view == "links_submenu":
            select = discord.ui.Select(
                placeholder="اختر الإجراء...",
                custom_id="links_submenu_select"
            )
            select.add_option(
                label="تفعيل حماية الروابط",
                value="enable_links",
                emoji=emojis_config.PROTECTION_EMOJIS['enable'],
                description="تفعيل حماية الروابط"
            )
            select.add_option(
                label="تعطيل حماية الروابط",
                value="disable_links",
                emoji=emojis_config.PROTECTION_EMOJIS['disable'],
                description="تعطيل حماية الروابط"
            )
            select.add_option(
                label="الرتب المستثناة",
                value="exempt_roles",
                emoji=emojis_config.PROTECTION_EMOJIS['exempt_roles'],
                description="اختر الرتب التي يمكنها نشر الروابط"
            )
            select.callback = self._on_links_submenu_select
            self.add_item(select)
            
            # Add back button
            back_btn = discord.ui.Button(
                label="رجوع للقائمة",
                style=discord.ButtonStyle.secondary,
                custom_id="links_back_btn",
                row=1
            )
            back_btn.emoji = emojis_config.NAV_EMOJIS['back']
            back_btn.callback = self._on_links_back_button
            self.add_item(back_btn)
            
        elif self.current_view == "anti_nuke":
            select = discord.ui.Select(
                placeholder="اختر الفئة...",
                custom_id="anti_nuke_select"
            )
            select.add_option(
                label="الكلمات المحظورة",
                value="words_penalties",
                emoji=emojis_config.PROTECTION_EMOJIS['banned_words'],
                description="تعيين عقوبات للكلمات المحظورة"
            )
            select.add_option(
                label="حماية الروابط",
                value="links_penalties",
                emoji=emojis_config.PROTECTION_EMOJIS['anti_links'],
                description="تعيين عقوبات للروابط"
            )
            select.callback = self._on_anti_nuke_select
            self.add_item(select)
            
            # Add back button
            back_btn = discord.ui.Button(
                label="رجوع للقائمة",
                style=discord.ButtonStyle.secondary,
                custom_id="anti_nuke_back_btn",
                row=1
            )
            back_btn.emoji = emojis_config.NAV_EMOJIS['back']
            back_btn.callback = self._on_anti_nuke_back_button
            self.add_item(back_btn)
    
    async def _on_main_back_button(self, interaction: discord.Interaction):
        """معالجة زر الرجوع للقائمة الرئيسية"""
        try:
            # Defer immediately to prevent timeout
            await interaction.response.defer()
            
            # If this is a shortcut, don't go back to step 3 - just close the view
            if self.is_shortcut:
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **تم إغلاق لوحة التحكم**",
                    view=None,
                    embeds=[]
                )
                return
            
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
                view=Step3SettingsView(self.bot),
                embeds=[]
            )
        except discord.NotFound:
            # Handle 404 Unknown Webhook errors - interaction expired
            try:
                if self.is_shortcut:
                    await interaction.channel.send(
                        f"{interaction.user.mention} **تم إغلاق لوحة التحكم**",
                        view=None
                    )
                else:
                    await interaction.channel.send(
                        f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
                        view=Step3SettingsView(self.bot)
                    )
            except Exception as e:
                print(f"[SystemBot] Error in _on_main_back_button fallback: {e}")
        except Exception as e:
            print(f"[SystemBot] Error in _on_main_back_button: {e}")
    
    async def _on_main_select(self, interaction: discord.Interaction):
        """معالجة اختيار القائمة الرئيسية"""
        value = interaction.data["values"][0]
        
        if value == "banned_words":
            self.current_view = "words_submenu"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **إدارة الكلمات المحظورة**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
        elif value == "anti_links":
            self.current_view = "links_submenu"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **حماية الروابط**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
        elif value == "anti_nuke":
            self.current_view = "anti_nuke"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **نظام مكافحة التخريب**\nاختر الفئة من القائمة أدناه:",
                view=self
            )
    
    async def _on_words_back_button(self, interaction: discord.Interaction):
        """معالجة زر الرجوع من قائمة الكلمات"""
        self.current_view = "main"
        self._update_menu_options()
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **إعداد نظام الحماية**\nحدد الكلمات المحظورة والعقوبات:",
            view=self
        )
    
    async def _on_words_submenu_select(self, interaction: discord.Interaction):
        """معالجة اختيار قائمة الكلمات"""
        value = interaction.data["values"][0]
        
        if value == "add_word":
            await self._add_banned_word(interaction)
        elif value == "remove_word":
            await self._remove_banned_word(interaction)
    
    async def _add_banned_word(self, interaction: discord.Interaction):
        """إضافة كلمة محظورة"""
        bd = self.bot._bot_dir
        
        # Edit message to show prompt
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **اكتب الكلمة المحظورة**\n(لإلغاء: اكتب `إلغاء`)",
            view=None
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            
            if msg.content.strip().lower() == 'إلغاء':
                await msg.delete()
                self.current_view = "words_submenu"
                self._update_menu_options()
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **إدارة الكلمات المحظورة**\nاختر الإجراء من القائمة أدناه:",
                    view=self
                )
                return
            
            word = msg.content.strip().lower()
            await msg.delete()
            
            # Add word to list
            words = cfg("prohibited_words", bd) or []
            if word not in words:
                words.append(word)
                set_cfg("prohibited_words", words, bd)
                reload_config_for(self.bot)
            
            self.current_view = "words_submenu"
            self._update_menu_options()
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **✅ تم إضافة الكلمة: {word}**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
            
        except asyncio.TimeoutError:
            self.current_view = "words_submenu"
            self._update_menu_options()
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **❌ انتهى الوقت. تم إلغاء العملية**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
    
    async def _remove_banned_word(self, interaction: discord.Interaction):
        """إزالة كلمة محظورة"""
        bd = self.bot._bot_dir
        words = cfg("prohibited_words", bd) or []
        
        if not words:
            self.current_view = "words_submenu"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **❌ لا توجد كلمات محظورة**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
            return
        
        # Create select menu for word removal
        self.clear_items()
        options = []
        for word in words[:25]:  # Discord limit
            options.append(discord.SelectOption(label=word, value=word))
        
        word_select = discord.ui.Select(
            placeholder="اختر الكلمة للحذف...",
            options=options,
            custom_id="remove_word_select"
        )
        
        async def remove_callback(interaction: discord.Interaction):
            selected_word = interaction.data["values"][0]
            if selected_word in words:
                words.remove(selected_word)
                set_cfg("prohibited_words", words, bd)
                reload_config_for(self.bot)
            
            self.current_view = "words_submenu"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **✅ تم حذف الكلمة: {selected_word}**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
        
        word_select.callback = remove_callback
        self.add_item(word_select)
        
        # Add back button
        back_btn = discord.ui.Button(
            label="رجوع للقائمة",
            style=discord.ButtonStyle.secondary,
            custom_id="remove_word_back_btn",
            row=1
        )
        back_btn.emoji = emojis_config.NAV_EMOJIS['back']
        
        async def back_callback(interaction: discord.Interaction):
            self.current_view = "words_submenu"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **إدارة الكلمات المحظورة**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
        
        back_btn.callback = back_callback
        self.add_item(back_btn)
        
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **اختر الكلمة للحذف**\nاختر الكلمة من القائمة أدناه:",
            view=self
        )
    
    async def _on_links_back_button(self, interaction: discord.Interaction):
        """معالجة زر الرجوع من قائمة الروابط"""
        self.current_view = "main"
        self._update_menu_options()
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **إعداد نظام الحماية**\nحدد الكلمات المحظورة والعقوبات:",
            view=self
        )
    
    async def _on_links_submenu_select(self, interaction: discord.Interaction):
        """معالجة اختيار قائمة الروابط"""
        value = interaction.data["values"][0]
        
        if value == "enable_links":
            await self._toggle_link_protection(interaction, True)
        elif value == "disable_links":
            await self._toggle_link_protection(interaction, False)
        elif value == "exempt_roles":
            await self._select_exempt_roles(interaction)
    
    async def _toggle_link_protection(self, interaction: discord.Interaction, enable: bool):
        """تفعيل/تعطيل حماية الروابط"""
        bd = self.bot._bot_dir
        p_cfg = _get_punishment_config(bd)
        
        if enable:
            # Add default link prefixes if not present
            if not p_cfg.get("link_prefixes"):
                p_cfg["link_prefixes"] = ["http", "https", "discord.gg"]
        else:
            # Clear link prefixes
            p_cfg["link_prefixes"] = []
        
        set_cfg("punishment_config", p_cfg, bd)
        reload_config_for(self.bot)
        
        status = "مُفعَّل" if enable else "معطّل"
        self.current_view = "links_submenu"
        self._update_menu_options()
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **✅ تم {status} حماية الروابط**\nاختر الإجراء من القائمة أدناه:",
            view=self
        )
    
    async def _select_exempt_roles(self, interaction: discord.Interaction):
        """اختيار الرتب المستثناة من حماية الروابط"""
        guild = interaction.guild
        bd = self.bot._bot_dir
        p_cfg = _get_punishment_config(bd)
        exempt_role_ids = p_cfg.get("exempt_role_ids", []) or []
        
        # Create RoleSelect for role selection (avoids 25 options limit)
        self.clear_items()
        
        role_select = discord.ui.RoleSelect(
            placeholder="اختر الرتب المستثناة...",
            custom_id="exempt_roles_select",
            min_values=0,
            max_values=25,
            row=0
        )
        
        # Pre-select currently exempt roles
        if exempt_role_ids:
            role_select.default_values = [discord.Object(id=rid) for rid in exempt_role_ids if guild.get_role(rid)]
        
        async def exempt_callback(interaction: discord.Interaction):
            selected_ids = [int(val) for val in interaction.data["values"]]
            p_cfg["exempt_role_ids"] = selected_ids
            set_cfg("punishment_config", p_cfg, bd)
            reload_config_for(self.bot)
            
            self.current_view = "links_submenu"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **✅ تم تحديث الرتب المستثناة**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
        
        role_select.callback = exempt_callback
        self.add_item(role_select)
        
        # Add back button
        back_btn = discord.ui.Button(
            label="رجوع للقائمة",
            style=discord.ButtonStyle.secondary,
            custom_id="exempt_roles_back_btn",
            row=1
        )
        back_btn.emoji = emojis_config.NAV_EMOJIS['back']
        
        async def back_callback(interaction: discord.Interaction):
            self.current_view = "links_submenu"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **حماية الروابط**\nاختر الإجراء من القائمة أدناه:",
                view=self
            )
        
        back_btn.callback = back_callback
        self.add_item(back_btn)
        
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **اختر الرتب المستثناة**\nاختر الرتب من القائمة أدناه:",
            view=self
        )
    
    async def _on_anti_nuke_back_button(self, interaction: discord.Interaction):
        """معالجة زر الرجوع من نظام مكافحة التخريب"""
        self.current_view = "main"
        self._update_menu_options()
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **إعداد نظام الحماية**\nحدد الكلمات المحظورة والعقوبات:",
            view=self
        )
    
    async def _on_anti_nuke_select(self, interaction: discord.Interaction):
        """معالجة اختيار نظام مكافحة التخريب"""
        value = interaction.data["values"][0]
        
        if value == "words_penalties":
            await self._set_word_penalties(interaction)
        elif value == "links_penalties":
            await self._set_link_penalties(interaction)
    
    async def _set_word_penalties(self, interaction: discord.Interaction):
        """تعيين عقوبات للكلمات المحظورة"""
        bd = self.bot._bot_dir
        words = cfg("prohibited_words", bd) or []
        
        if not words:
            self.current_view = "anti_nuke"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **❌ لا توجد كلمات محظورة**\nاختر الفئة من القائمة أدناه:",
                view=self
            )
            return
        
        # Create select menu for word selection
        self.clear_items()
        options = []
        for word in words[:25]:  # Discord limit
            options.append(discord.SelectOption(label=word, value=word))
        
        word_select = discord.ui.Select(
            placeholder="اختر الكلمة لتعيين العقوبة...",
            options=options,
            custom_id="word_penalty_select"
        )
        
        async def word_penalty_callback(interaction: discord.Interaction):
            selected_word = interaction.data["values"][0]
            await self._select_penalty_type(interaction, selected_word, "word")
        
        word_select.callback = word_penalty_callback
        self.add_item(word_select)
        
        # Add back button
        back_btn = discord.ui.Button(
            label="رجوع للقائمة",
            style=discord.ButtonStyle.secondary,
            custom_id="word_penalty_back_btn",
            row=1
        )
        back_btn.emoji = emojis_config.NAV_EMOJIS['back']
        
        async def back_callback(interaction: discord.Interaction):
            self.current_view = "anti_nuke"
            self._update_menu_options()
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} **نظام مكافحة التخريب**\nاختر الفئة من القائمة أدناه:",
                view=self
            )
        
        back_btn.callback = back_callback
        self.add_item(back_btn)
        
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **اختر الكلمة لتعيين العقوبة**\nاختر الكلمة من القائمة أدناه:",
            view=self
        )
    
    async def _set_link_penalties(self, interaction: discord.Interaction):
        """تعيين عقوبات للروابط"""
        await self._select_penalty_type(interaction, "links", "link")
    
    async def _select_penalty_type(self, interaction: discord.Interaction, target: str, target_type: str):
        """اختيار نوع العقوبة"""
        self.clear_items()
        
        select = discord.ui.Select(
            placeholder="اختر نوع العقوبة...",
            custom_id="penalty_type_select"
        )
        select.add_option(
            label="كتم",
            value="mute",
            emoji=emojis_config.PROTECTION_EMOJIS['mute'],
            description="كتم صوتي للمخالف"
        )
        select.add_option(
            label="سجن",
            value="jail",
            emoji=emojis_config.PROTECTION_EMOJIS['jail'],
            description="سجن للمخالف"
        )
        
        async def penalty_type_callback(interaction: discord.Interaction):
            penalty_type = interaction.data["values"][0]
            await self._select_penalty_duration(interaction, target, target_type, penalty_type)
        
        select.callback = penalty_type_callback
        self.add_item(select)
        
        # Add back button
        back_btn = discord.ui.Button(
            label="رجوع للقائمة",
            style=discord.ButtonStyle.secondary,
            custom_id="penalty_type_back_btn",
            row=1
        )
        back_btn.emoji = emojis_config.NAV_EMOJIS['back']
        
        async def back_callback(interaction: discord.Interaction):
            if target_type == "word":
                await self._set_word_penalties(interaction)
            else:
                self.current_view = "anti_nuke"
                self._update_menu_options()
                await interaction.response.edit_message(
                    content=f"{interaction.user.mention} **نظام مكافحة التخريب**\nاختر الفئة من القائمة أدناه:",
                    view=self
                )
        
        back_btn.callback = back_callback
        self.add_item(back_btn)
        
        target_text = f"الكلمة: {target}" if target_type == "word" else "الروابط"
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **اختر نوع العقوبة لـ {target_text}**\nاختر نوع العقوبة من القائمة أدناه:",
            view=self
        )
    
    async def _select_penalty_duration(self, interaction: discord.Interaction, target: str, target_type: str, penalty_type: str):
        """اختيار مدة العقوبة"""
        # Edit message to show prompt
        penalty_text = "كتم" if penalty_type == "mute" else "سجن"
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **اكتب مدة {penalty_text}**\n(مثال: 10min أو 2h أو 5d أو 1m)\n(ملاحظة: min=دقائق، h=ساعات، d=أيام، m=أشهر)\n(لإلغاء: اكتب `إلغاء`)",
            view=None
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            
            if msg.content.strip().lower() == 'إلغاء':
                await msg.delete()
                await self._select_penalty_type(interaction, target, target_type)
                return
            
            duration = msg.content.strip()
            await msg.delete()
            
            # Save penalty configuration
            bd = self.bot._bot_dir
            p_cfg = _get_punishment_config(bd)
            
            if target_type == "word":
                if "word_penalties" not in p_cfg:
                    p_cfg["word_penalties"] = {}
                p_cfg["word_penalties"][target] = {
                    "type": penalty_type,
                    "duration": duration
                }
            else:  # link
                p_cfg["link_penalty"] = {
                    "type": penalty_type,
                    "duration": duration
                }
            
            set_cfg("punishment_config", p_cfg, bd)
            reload_config_for(self.bot)
            
            self.current_view = "anti_nuke"
            self._update_menu_options()
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **✅ تم حفظ العقوبة**\nاختر الفئة من القائمة أدناه:",
                view=self
            )
            
        except asyncio.TimeoutError:
            self.current_view = "anti_nuke"
            self._update_menu_options()
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **❌ انتهى الوقت. تم إلغاء العملية**\nاختر الفئة من القائمة أدناه:",
                view=self
            )


# ────────────────────────────────────────────────────────────────────────────
# 5️⃣  الرول التلقائي
# ────────────────────────────────────────────────────────────────────────────
def _feature_autorole_embed(bot_ref, guild: discord.Guild) -> discord.Embed:
    bd     = bot_ref._bot_dir
    ar_id  = cfg("auto_role", bd)
    ar     = guild.get_role(int(ar_id)).mention if ar_id and guild.get_role(int(ar_id)) else "⬜ لم تُحدَّد"
    enabled = bool(cfg("feature_auto_role", bd))
    return _embed(
        "🤖  إعداد الرول التلقائي",
        f"**الحالة:** {'🟢 مُفعَّل' if enabled else '🔴 معطّل'}\n"
        f"**الرول التلقائي:** {ar}\n"
        f"{_sep()}"
        "الرول الذي يُعطى تلقائياً لكل عضو جديد يدخل السيرفر.",
        C.SUCCESS,
        footer="System Bot  •  ⚙️ الرول التلقائي  •  v6.0"
    )


class FeatureAutoRoleView(View):
    def __init__(self, bot_ref, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.is_shortcut = is_shortcut

        role_sel = discord.ui.RoleSelect(
            placeholder="🎭  اختر الرول التلقائي...",
            custom_id="far_role_v6", row=0,
            min_values=1, max_values=1)
        role_sel.callback = self._on_role_select
        self.add_item(role_sel)

        # Back button - only add if not a shortcut
        if not self.is_shortcut:
            back_btn = discord.ui.Button(label="🔙  رجوع للقائمة", style=discord.ButtonStyle.secondary,
                                         custom_id="far_back_v6", row=1)
            back_btn.callback = self.back_btn
            self.add_item(back_btn)

    async def _on_role_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔", ephemeral=True)
        role_id = int(interaction.data["values"][0])
        set_cfg("auto_role", role_id, self.bot._bot_dir)
        reload_config_for(self.bot)
        role = interaction.guild.get_role(role_id)
        await interaction.edit_original_response(
            embed=_feature_autorole_embed(self.bot, interaction.guild), view=self)
        await interaction.followup.send(
            embed=_embed("✅ تم", f"الرول التلقائي: {role.mention if role else role_id}", C.SUCCESS),
            ephemeral=True)

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        try:
            # Defer immediately to prevent timeout
            await interaction.response.defer()
            
            # If this is a shortcut, don't go back to step 3 - just close the view
            if self.is_shortcut:
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **تم إغلاق لوحة التحكم**",
                    view=None,
                    embeds=[]
                )
                return
            
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
                view=Step3SettingsView(self.bot, interaction.user.id),
                embeds=[])
        except discord.NotFound:
            # Handle 404 Unknown Webhook errors - interaction expired
            print(f"[SystemBot] Interaction expired in FeatureAutoRoleView back button")
        except Exception as e:
            print(f"[SystemBot] Error in FeatureAutoRoleView back button: {e}")


# ────────────────────────────────────────────────────────────────────────────
# 🔓  نظام الرياكشن (Reaction Room Unlock) — ميزة جديدة
# ────────────────────────────────────────────────────────────────────────────
def _feature_reaction_room_embed(bot_ref, guild: discord.Guild) -> discord.Embed:
    bd = bot_ref._bot_dir
    ch_id = cfg("reaction_room_channel", bd)
    ch = guild.get_channel(int(ch_id)).mention if ch_id and guild.get_channel(int(ch_id)) else "⬜ لم تُحدَّد"
    writer_role_id = cfg("reaction_room_writer_role", bd)
    writer_role = guild.get_role(int(writer_role_id)).mention if writer_role_id and guild.get_role(int(writer_role_id)) else "⬜ لم تُحدَّد"
    emoji = cfg("reaction_room_emoji", bd) or "⬜ لم تُحدَّد"
    member_role_id = cfg("reaction_room_member_role", bd)
    member_role = guild.get_role(int(member_role_id)).mention if member_role_id and guild.get_role(int(member_role_id)) else "⬜ لم تُحدَّد"
    
    return _embed(
        "🔓  إعداد نظام الرياكشن",
        f"**روم الرياكشن:** {ch}\n"
        f"**رتبة الكاتب:** {writer_role}\n"
        f"**الرياكشن:** {emoji}\n"
        f"**رتبة العضو:** {member_role}\n"
        f"{_sep()}"
        "استخدم الأزرار أدناه لضبط إعدادات نظام فتح السيرفر بالرياكشن.",
        C.INFO,
        footer="System Bot  •  🔓 نظام الرياكشن  •  v1.0"
    )


class FeatureReactionRoomView(View):
    def __init__(self, bot_ref, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.is_shortcut = is_shortcut
        self.state = 0  # 0: channel, 1: writer_role, 2: emoji, 3: member_role
        self._update_view()

    def _update_view(self):
        self.clear_items()
        
        if self.state == 0:
            # Channel selection
            ch_sel = discord.ui.ChannelSelect(
                placeholder="اختر روم الرياكشن...",
                custom_id="frr_channel_v1", row=0,
                channel_types=[discord.ChannelType.text])
            ch_sel.callback = self._on_channel_select
            self.add_item(ch_sel)
        elif self.state == 1:
            # Writer role selection
            role_sel = discord.ui.RoleSelect(
                placeholder="اختر رتبة الكاتب...",
                custom_id="frr_writer_role_v1", row=0,
                min_values=1, max_values=1)
            role_sel.callback = self._on_writer_role_select
            self.add_item(role_sel)
        elif self.state == 2:
            # Emoji - ask to send message
            btn = discord.ui.Button(
                label="إرسال الرياكشن كرسالة",
                style=discord.ButtonStyle.primary,
                custom_id="frr_emoji_btn_v1", row=0)
            btn.callback = self._on_emoji_btn
            self.add_item(btn)
        elif self.state == 3:
            # Member role selection
            role_sel = discord.ui.RoleSelect(
                placeholder="اختر رتبة العضو...",
                custom_id="frr_member_role_v1", row=0,
                min_values=1, max_values=1)
            role_sel.callback = self._on_member_role_select
            self.add_item(role_sel)
        
        # Back button - only add if not a shortcut
        if not self.is_shortcut:
            back_btn = discord.ui.Button(
                label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                custom_id="frr_back_v1", row=1)
            back_btn.callback = self._on_back
            self.add_item(back_btn)

    async def _on_channel_select(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔", ephemeral=True)
        ch_id = int(interaction.data["values"][0])
        set_cfg("reaction_room_channel", ch_id, self.bot._bot_dir)
        reload_config_for(self.bot)
        # Update state BEFORE rebuilding view
        self.state = 1
        self._update_view()
        # Now edit with the updated view
        await interaction.edit_original_response(
            embed=_feature_reaction_room_embed(self.bot, interaction.guild),
            view=self)
        await interaction.followup.send("✅ تم تحديد روم الرياكشن", ephemeral=True)

    async def _on_writer_role_select(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔", ephemeral=True)
        role_id = int(interaction.data["values"][0])
        set_cfg("reaction_room_writer_role", role_id, self.bot._bot_dir)
        reload_config_for(self.bot)
        # Update state BEFORE rebuilding view
        self.state = 2
        self._update_view()
        # Now edit with the updated view
        await interaction.edit_original_response(
            embed=_feature_reaction_room_embed(self.bot, interaction.guild),
            view=self)
        await interaction.followup.send("✅ تم تحديد رتبة الكاتب", ephemeral=True)

    async def _on_emoji_btn(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout during message waiting
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔", ephemeral=True)
        
        await interaction.followup.send(
            "📝 أرسل الرياكشن كرسالة في الشات الآن...",
            ephemeral=True)
        
        # Wait for message with emoji
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30)
            
            # Handle cancellation
            if msg.content.strip().lower() == 'إلغاء':
                await msg.delete()
                await interaction.followup.send("❌ تم إلغاء العملية", ephemeral=True)
                # Restore the view
                self.state = 2
                self._update_view()
                await interaction.edit_original_response(
                    embed=_feature_reaction_room_embed(self.bot, interaction.guild),
                    view=self
                )
                return
            
            emoji_str = msg.content.strip()
            if emoji_str:
                set_cfg("reaction_room_emoji", emoji_str, self.bot._bot_dir)
                reload_config_for(self.bot)
                await interaction.followup.send(f"✅ تم تحديد الرياكيون: {emoji_str}", ephemeral=True)
                # Update state BEFORE rebuilding view
                self.state = 3
                self._update_view()
                # Now edit with the updated view
                await interaction.edit_original_response(
                    embed=_feature_reaction_room_embed(self.bot, interaction.guild),
                    view=self)
            else:
                await interaction.followup.send("❌ الرياكيون فارغ", ephemeral=True)
        except Exception:
            await interaction.followup.send("⏰ انتهى الوقت أو حدث خطأ", ephemeral=True)

    async def _on_member_role_select(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔", ephemeral=True)
        role_id = int(interaction.data["values"][0])
        set_cfg("reaction_room_member_role", role_id, self.bot._bot_dir)
        reload_config_for(self.bot)
        await interaction.edit_original_response(
            embed=_feature_reaction_room_embed(self.bot, interaction.guild),
            view=self)
        await interaction.followup.send("✅ تم تحديد رتبة العضو", ephemeral=True)

    async def _on_back(self, interaction: discord.Interaction):
        try:
            # Defer immediately to prevent timeout
            await interaction.response.defer()
            
            if self.state > 0:
                self.state -= 1
                self._update_view()
                await interaction.edit_original_response(
                    embed=_feature_reaction_room_embed(self.bot, interaction.guild),
                    view=self)
            else:
                # If this is a shortcut, don't go back to step 3 - just close the view
                if self.is_shortcut:
                    await interaction.edit_original_response(
                        content=f"{interaction.user.mention} **تم إغلاق لوحة التحكم**",
                        view=None,
                        embeds=[]
                    )
                    return
                
                await _back_to_step3(self.bot, interaction)
        except discord.NotFound:
            # Handle 404 Unknown Webhook errors - interaction expired
            try:
                if self.state > 0:
                    self.state -= 1
                    self._update_view()
                    await interaction.channel.send(
                        embed=_feature_reaction_room_embed(self.bot, interaction.guild),
                        view=self)
                else:
                    if self.is_shortcut:
                        await interaction.channel.send(
                            f"{interaction.user.mention} **تم إغلاق لوحة التحكم**",
                            view=None
                        )
                    else:
                        await interaction.channel.send(
                            f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
                            view=Step3SettingsView(self.bot, interaction.user.id)
                        )
            except Exception as e:
                print(f"[SystemBot] Error in _on_back fallback: {e}")
        except Exception as e:
            print(f"[SystemBot] Error in _on_back: {e}")


# ────────────────────────────────────────────────────────────────────────────
# 6️⃣  الرتب التفاعلية (Self Roles) — ميزة جديدة v6.0
# ────────────────────────────────────────────────────────────────────────────
def _get_self_roles_config(bot_dir=None) -> dict:
    """يرجع dict: {str(role_id): {"label": str, "emoji": str, "description": str}}"""
    data = cfg("self_roles_config", bot_dir)
    if isinstance(data, dict):
        return data
    return {}


def _feature_selfroles_embed(bot_ref, guild: discord.Guild) -> discord.Embed:
    bd      = bot_ref._bot_dir
    src_id  = cfg("self_roles_channel", bd)
    src_ch  = guild.get_channel(int(src_id)).mention if src_id and guild.get_channel(int(src_id)) else "⬜ لم تُحدَّد"
    enabled = bool(cfg("feature_self_roles", bd))
    sr_cfg  = _get_self_roles_config(bd)

    lines = []
    for rid_str, rdata in sr_cfg.items():
        role = guild.get_role(int(rid_str))
        label = rdata.get("label", "—")
        emoji = rdata.get("emoji", "🎭")
        if role:
            lines.append(f"{emoji} **{label}** → {role.mention}")
        else:
            lines.append(f"{emoji} **{label}** → `{rid_str}` (محذوفة)")

    roles_text = "\n".join(lines) if lines else "⬜ لا توجد رتب مُضافة بعد"

    return _embed(
        "🎭  إعداد الرتب التفاعلية",
        f"**الحالة:** {'🟢 مُفعَّل' if enabled else '🔴 معطّل'}\n"
        f"**روم الأزرار:** {src_ch}\n"
        f"{_sep()}"
        f"**الرتب الحالية في النظام:**\n{roles_text}\n"
        f"{_sep()}"
        "أضف رتبة جديدة أو احذف رتبة موجودة، ثم اضغط **نشر الأزرار** لإرسال لوحة الرتب.",
        C.PURPLE,
        footer="System Bot  •  ⚙️ الرتب التفاعلية  •  v6.0"
    )


class FeatureSelfRolesView(View):
    """واجهة إعداد الرتب التفاعلية الجديدة"""
    def __init__(self, bot_ref, caller_id: int = None, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.caller_id = int(caller_id) if caller_id else None
        self.is_shortcut = is_shortcut
        
        menu_options = [
            discord.SelectOption(label="إضافة رول تفاعلي", value="add", description="إضافة رول جديد مع صلاحيات", emoji=emojis_config.SELF_ROLES_EMOJIS.get("add")),
            discord.SelectOption(label="حذف رول تفاعلي", value="delete", description="حذف رول تفاعلي موجود", emoji=emojis_config.SELF_ROLES_EMOJIS.get("delete")),
            discord.SelectOption(label="تعديل رول تفاعلي", value="edit", description="تعديل صلاحيات رول موجود", emoji=emojis_config.SELF_ROLES_EMOJIS.get("edit")),
            discord.SelectOption(label="إنشاء رول خاص", value="custom", description="إنشاء رول شخصي لعضو", emoji=emojis_config.SELF_ROLES_EMOJIS.get("custom")),
            discord.SelectOption(label="عرض الرتب التفاعلية", value="view", description="عرض جميع الرتب التفاعلية", emoji=emojis_config.SELF_ROLES_EMOJIS.get("view")),
        ]
        
        menu = discord.ui.Select(
            placeholder="اختر إجراء للرتب التفاعلية...",
            options=menu_options,
            custom_id="self_roles_menu",
            row=0
        )
        menu.callback = self._on_menu_select
        self.add_item(menu)

        # Back button - only add if not a shortcut
        if not self.is_shortcut:
            back_btn = discord.ui.Button(label="🔙 رجوع للقائمة", style=discord.ButtonStyle.secondary,
                                         custom_id="sr_main_back_btn", row=1, emoji=emojis_config.SELF_ROLES_EMOJIS.get("back"))
            back_btn.callback = self.back_btn
            self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "❌ فقط الشخص الذي استدعى الأمر يمكنه استخدام هذه القائمة.",
                ephemeral=True
            )
            return False
        return True

    async def _on_menu_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            choice = interaction.data["values"][0]

            if choice == "add":
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **إضافة رول تفاعلي**\nمنشن الرول أو أرسل الـ ID:",
                    view=InteractiveRoleAddView(self.bot, interaction.guild, self.caller_id, self.is_shortcut),
                    embeds=[])
            elif choice == "delete":
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **حذف رول تفاعلي**\nاختر الرول للحذف:",
                    view=InteractiveRoleDeleteView(self.bot, interaction.guild, self.caller_id, self.is_shortcut),
                    embeds=[])
            elif choice == "edit":
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **تعديل رول تفاعلي**\nاختر الرول للتعديل:",
                    view=InteractiveRoleEditView(self.bot, interaction.guild, self.caller_id, self.is_shortcut),
                    embeds=[])
            elif choice == "custom":
                # Start chat input for role name
                role_name = await _get_role_name_from_chat(
                    self.bot,
                    interaction,
                    "اكتب اسم الرول الخاص في الشات الآن:",
                    CustomRoleNameView,
                    interaction.guild,
                    self.caller_id,
                    self.is_shortcut
                )
                if role_name:
                    # Update the message directly (not interaction.response)
                    prompt_message = await interaction.original_response()
                    await prompt_message.edit(
                        content=f"{interaction.user.mention} اختار مالك الرول الخاص:",
                        view=CustomRoleOwnerView(self.bot, interaction.guild, role_name, self.caller_id, self.is_shortcut),
                        embeds=[]
                    )
            elif choice == "view":
                await self._view_roles(interaction)
        except Exception as e:
            print(f"[FeatureSelfRolesView] Error in _on_menu_select: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass

    async def _view_roles(self, interaction: discord.Interaction):
        try:
            bd = self.bot._bot_dir
            roles_cfg = cfg("interactive_roles", bd) or {}

            if not roles_cfg:
                return await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **الرتب التفاعلية**\nلا توجد رتب تفاعلية مسجلة.",
                    view=FeatureSelfRolesView(self.bot, self.caller_id),
                    embeds=[])

            lines = []
            for role_id, data in roles_cfg.items():
                role = interaction.guild.get_role(int(role_id))
                role_name = role.name if role else f"ID:{role_id}"
                perms = data.get("permissions", [])
                channels = data.get("channels", [])
                lines.append(f"• {role_name}: {', '.join(perms)} | الرومات: {', '.join(channels) if channels else 'الكل'}")

            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **الرتب التفاعلية**\n" + "\n".join(lines),
                view=FeatureSelfRolesView(self.bot, self.caller_id, self.is_shortcut),
                embeds=[])
        except Exception as e:
            print(f"[FeatureSelfRolesView] Error in _view_roles: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        try:
            # Defer immediately to prevent timeout
            await interaction.response.defer()

            # If this is a shortcut, don't go back to step 3 - just close the view
            if self.is_shortcut:
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **تم إغلاق لوحة التحكم**",
                    view=None,
                    embeds=[]
                )
                return

            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
                embeds=[],
                view=Step3SettingsView(self.bot, self.caller_id))
        except Exception as e:
            print(f"[FeatureSelfRolesView] Error in back_btn: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass


class InteractiveRoleAddView(View):
    """إضافة رول تفاعلي"""
    def __init__(self, bot_ref, guild, caller_id: int = None, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.guild = guild
        self.caller_id = int(caller_id) if caller_id else None
        self.is_shortcut = is_shortcut
        
        role_select = discord.ui.RoleSelect(
            placeholder="اختر الرول...",
            custom_id="ira_role_select",
            row=0
        )
        role_select.callback = self._on_role_select
        self.add_item(role_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "❌ فقط الشخص الذي استدعى الأمر يمكنه استخدام هذه القائمة.",
                ephemeral=True
            )
            return False
        return True

    async def _on_role_select(self, interaction: discord.Interaction):
        try:
            # Defer interaction first to prevent timeout
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            
            if not interaction.user.guild_permissions.administrator:
                return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
            
            role_id = interaction.data["values"][0]
            
            # Get original message to edit
            prompt_message = await interaction.original_response()
            await prompt_message.edit(
                content=f"{interaction.user.mention} **اختر الصلاحيات للرول**",
                view=InteractiveRolePermsView(self.bot, role_id, self.guild, self.caller_id, self.is_shortcut),
                embeds=[]
            )
        except discord.HTTPException as e:
            print(f"[InteractiveRoleAddView] HTTPException in _on_role_select: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ خطأ في اختيار الرول: {e}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ خطأ في اختيار الرول: {e}", ephemeral=True)
            except:
                pass
        except Exception as e:
            print(f"[InteractiveRoleAddView] Error in _on_role_select: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ حدث خطأ: {e}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="ira_back", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} اختر إجراء للرتب التفاعلية:",
            view=FeatureSelfRolesView(self.bot, self.caller_id, self.is_shortcut),
            embeds=[])


class InteractiveRolePermsView(View):
    """اختيار صلاحيات الرول التفاعلي - Full Discord Permissions"""
    def __init__(self, bot_ref, role_id, guild, caller_id: int = None, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.role_id = role_id
        self.guild = guild
        self.caller_id = int(caller_id) if caller_id else None
        self.is_shortcut = is_shortcut
        
        # Full Discord permissions
        perm_options = [
            discord.SelectOption(label="Administrator", value="administrator", description="All permissions"),
            discord.SelectOption(label="Manage Channels", value="manage_channels", description="Manage server channels"),
            discord.SelectOption(label="Manage Roles", value="manage_roles", description="Manage server roles"),
            discord.SelectOption(label="Manage Messages", value="manage_messages", description="Manage messages"),
            discord.SelectOption(label="Manage Webhooks", value="manage_webhooks", description="Manage webhooks"),
            discord.SelectOption(label="Kick Members", value="kick_members", description="Kick members"),
            discord.SelectOption(label="Ban Members", value="ban_members", description="Ban members"),
            discord.SelectOption(label="Moderate Members", value="moderate_members", description="Timeout members"),
            discord.SelectOption(label="Read Messages", value="read_messages", description="Read messages"),
            discord.SelectOption(label="Send Messages", value="send_messages", description="Send messages"),
            discord.SelectOption(label="Embed Links", value="embed_links", description="Embed links"),
            discord.SelectOption(label="Attach Files", value="attach_files", description="Attach files"),
            discord.SelectOption(label="Add Reactions", value="add_reactions", description="Add reactions"),
            discord.SelectOption(label="Mention Everyone", value="mention_everyone", description="Mention @everyone"),
            discord.SelectOption(label="Connect", value="connect", description="Connect to voice"),
            discord.SelectOption(label="Speak", value="speak", description="Speak in voice"),
            discord.SelectOption(label="Mute Members", value="mute_members", description="Mute members"),
            discord.SelectOption(label="Deafen Members", value="deafen_members", description="Deafen members"),
            discord.SelectOption(label="Move Members", value="move_members", description="Move members"),
            discord.SelectOption(label="Priority Speaker", value="priority_speaker", description="Priority speaker"),
            discord.SelectOption(label="View Channel", value="view_channel", description="View channels"),
            discord.SelectOption(label="Send TTS Messages", value="send_tts_messages", description="Send TTS messages"),
            discord.SelectOption(label="Use External Emojis", value="use_external_emojis", description="Use external emojis"),
            discord.SelectOption(label="Use Application Commands", value="use_application_commands", description="Use slash commands"),
            discord.SelectOption(label="Request to Speak", value="request_to_speak", description="Request to speak"),
            discord.SelectOption(label="Manage Events", value="manage_events", description="Manage events"),
            discord.SelectOption(label="Manage Threads", value="manage_threads", description="Manage threads"),
            discord.SelectOption(label="Create Public Threads", value="create_public_threads", description="Create public threads"),
            discord.SelectOption(label="Create Private Threads", value="create_private_threads", description="Create private threads"),
            discord.SelectOption(label="Use External Stickers", value="use_external_stickers", description="Use external stickers"),
            discord.SelectOption(label="Send Messages in Threads", value="send_messages_in_threads", description="Send in threads"),
        ]
        
        # Discord requires 1-25 options per Select Menu
        if len(perm_options) > 25:
            perm_options = perm_options[:25]
        elif len(perm_options) == 0:
            perm_options = [discord.SelectOption(label="لا يوجد صلاحيات متاحة", value="none")]
        
        perm_select = discord.ui.Select(
            placeholder="اختر الصلاحيات (يمكن اختيار أكثر من واحدة)...",
            options=perm_options,
            custom_id="irp_select",
            row=0,
            min_values=1,
            max_values=25
        )
        perm_select.callback = self._on_perm_select
        self.add_item(perm_select)

        # Back button
        back_btn = discord.ui.Button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                                     custom_id="irp_back", row=1)
        back_btn.callback = self.back_btn
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "❌ فقط الشخص الذي استدعى الأمر يمكنه استخدام هذه القائمة.",
                ephemeral=True
            )
            return False
        return True

    async def _on_perm_select(self, interaction: discord.Interaction):
        try:
            # Defer interaction first to prevent timeout
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)

            if not interaction.user.guild_permissions.administrator:
                return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)

            self.selected_perms = interaction.data["values"]

            # Get original message to edit
            prompt_message = await interaction.original_response()
            await prompt_message.edit(
                content=f"{interaction.user.mention} **اختر الرومات المسموح بها**",
                view=InteractiveRoleChannelsView(self.bot, self.role_id, self.selected_perms, self.guild, self.caller_id, self.is_shortcut),
                embeds=[]
            )
        except discord.HTTPException as e:
            print(f"[InteractiveRolePermsView] HTTPException in _on_perm_select: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(f"❌ خطأ في اختيار الصلاحيات: {e}", ephemeral=True)
            except:
                pass
        except Exception as e:
            print(f"[InteractiveRolePermsView] Error in _on_perm_select: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد الرتب التفاعلية**\nاختر إجراء للرتب التفاعلية:",
                embeds=[],
                view=FeatureSelfRolesView(self.bot, self.caller_id, self.is_shortcut)
            )
        except Exception as e:
            print(f"[InteractiveRolePermsView] Error in back_btn: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass


class InteractiveRoleChannelsView(View):
    """اختيار الرومات المسموح بها"""
    def __init__(self, bot_ref, role_id, permissions, guild, caller_id: int = None, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.role_id = role_id
        self.permissions = permissions
        self.guild = guild
        self.caller_id = int(caller_id) if caller_id else None
        self.is_shortcut = is_shortcut
        
        channel_options = [discord.SelectOption(label="جميع الرومات", value="all", description="السماح في جميع الرومات")]
        for channel in guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                channel_options.append(discord.SelectOption(label=channel.name, value=str(channel.id)))
        
        # Discord requires 1-25 options per Select Menu
        if len(channel_options) > 25:
            channel_options = channel_options[:25]
        elif len(channel_options) == 0:
            channel_options = [discord.SelectOption(label="لا يوجد رومات متاحة", value="none")]
        
        channel_select = discord.ui.Select(
            placeholder="اختر الرومات (يمكن اختيار أكثر من واحدة)...",
            options=channel_options,
            custom_id="irc_select",
            row=0,
            min_values=1,
            max_values=25
        )
        channel_select.callback = self._on_channel_select
        self.add_item(channel_select)

        # Back button
        back_btn = discord.ui.Button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                                     custom_id="irc_back", row=1)
        back_btn.callback = self.back_btn
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "❌ فقط الشخص الذي استدعى الأمر يمكنه استخدام هذه القائمة.",
                ephemeral=True
            )
            return False
        return True

    async def _on_channel_select(self, interaction: discord.Interaction):
        try:
            # Defer interaction first to prevent timeout
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)

            if not interaction.user.guild_permissions.administrator:
                return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)

            selected_channels = interaction.data["values"]

            # Save configuration and sync Discord permissions
            bd = self.bot._bot_dir
            roles_cfg = cfg("interactive_roles", bd) or {}

            # Build Discord permissions object
            permissions = discord.Permissions()
            for perm in self.permissions:
                setattr(permissions, perm, True)

            # Update the actual Discord role permissions
            role = self.guild.get_role(int(self.role_id))
            if role:
                try:
                    await role.edit(permissions=permissions)
                except Exception as e:
                    await interaction.followup.send(f"❌ خطأ في تحديث صلاحيات الرول: {e}", ephemeral=True)
                    return

            # Store the configuration
            roles_cfg[str(self.role_id)] = {
                "permissions": self.permissions,
                "channels": selected_channels
            }
            set_cfg("interactive_roles", roles_cfg, bd)

            # Get original message to edit
            prompt_message = await interaction.original_response()
            await prompt_message.edit(
                content=f"{interaction.user.mention} **تم حفظ الإعدادات**\nالصلاحيات: {', '.join(self.permissions)}\nالرومات: {', '.join(selected_channels)}",
                view=FeatureSelfRolesView(self.bot, self.caller_id),
                embeds=[]
            )
        except discord.HTTPException as e:
            print(f"[InteractiveRoleChannelsView] HTTPException in _on_channel_select: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(f"❌ خطأ في اختيار الرومات: {e}", ephemeral=True)
            except:
                pass
        except Exception as e:
            print(f"[InteractiveRoleChannelsView] Error in _on_channel_select: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **اختر الصلاحيات للرول**",
                embeds=[],
                view=InteractiveRolePermsView(self.bot, self.role_id, self.guild, self.caller_id)
            )
        except Exception as e:
            print(f"[InteractiveRoleChannelsView] Error in back_btn: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass


class InteractiveRoleDeleteView(View):
    """حذف رول تفاعلي"""
    def __init__(self, bot_ref, guild, caller_id: int = None, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.guild = guild
        self.caller_id = int(caller_id) if caller_id else None
        self.is_shortcut = is_shortcut
        
        bd = bot_ref._bot_dir
        roles_cfg = cfg("interactive_roles", bd) or {}
        
        options = []
        for role_id in roles_cfg.keys():
            role = guild.get_role(int(role_id))
            if role:
                options.append(discord.SelectOption(label=role.name, value=role_id))
        
        # Discord requires 1-25 options per Select Menu
        if len(options) > 25:
            options = options[:25]
        elif len(options) == 0:
            options = [discord.SelectOption(label="لا توجد رتب", value="none")]
        
        select = discord.ui.Select(
            placeholder="اختر الرول للحذف...",
            options=options,
            custom_id="ird_select",
            row=0
        )
        select.callback = self._on_select
        self.add_item(select)

        # Back button
        back_btn = discord.ui.Button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                                     custom_id="sr_delete_back_btn", row=1)
        back_btn.callback = self.back_btn
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "❌ فقط الشخص الذي استدعى الأمر يمكنه استخدام هذه القائمة.",
                ephemeral=True
            )
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        try:
            # Defer interaction first to prevent timeout
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)

            if not interaction.user.guild_permissions.administrator:
                return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)

            role_id = interaction.data["values"][0]
            if role_id == "none":
                prompt_message = await interaction.original_response()
                await prompt_message.edit(
                    content=f"{interaction.user.mention} لا توجد رتفاع للحذف",
                    view=FeatureSelfRolesView(self.bot, self.caller_id),
                    embeds=[]
                )
                return

            bd = self.bot._bot_dir
            roles_cfg = cfg("interactive_roles", bd) or {}
            if role_id in roles_cfg:
                del roles_cfg[role_id]
                set_cfg("interactive_roles", roles_cfg, bd)

            prompt_message = await interaction.original_response()
            await prompt_message.edit(
                content=f"{interaction.user.mention} تم حذف الرول بنجاح",
                view=FeatureSelfRolesView(self.bot, self.caller_id),
                embeds=[]
            )
        except discord.HTTPException as e:
            print(f"[InteractiveRoleDeleteView] HTTPException in _on_select: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(f"❌ خطأ في حذف الرول: {e}", ephemeral=True)
            except:
                pass
        except Exception as e:
            print(f"[InteractiveRoleDeleteView] Error in _on_select: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد الرتب التفاعلية**\nاختر إجراء للرتب التفاعلية:",
                embeds=[],
                view=FeatureSelfRolesView(self.bot, self.caller_id, self.is_shortcut)
            )
        except Exception as e:
            print(f"[InteractiveRoleDeleteView] Error in back_btn: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass


class InteractiveRoleEditView(View):
    """تعديل رول تفاعلي"""
    def __init__(self, bot_ref, guild, caller_id: int = None, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.guild = guild
        self.caller_id = int(caller_id) if caller_id else None
        self.is_shortcut = is_shortcut
        
        bd = bot_ref._bot_dir
        roles_cfg = cfg("interactive_roles", bd) or {}
        
        options = []
        for role_id in roles_cfg.keys():
            role = guild.get_role(int(role_id))
            if role:
                options.append(discord.SelectOption(label=role.name, value=role_id))
        
        # Discord requires 1-25 options per Select Menu
        if len(options) > 25:
            options = options[:25]
        elif len(options) == 0:
            options = [discord.SelectOption(label="لا توجد رتب", value="none")]
        
        select = discord.ui.Select(
            placeholder="اختر الرول للتعديل...",
            options=options,
            custom_id="ire_select",
            row=0
        )
        select.callback = self._on_select
        self.add_item(select)

        # Back button
        back_btn = discord.ui.Button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                                     custom_id="sr_edit_back_btn", row=1)
        back_btn.callback = self.back_btn
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "❌ فقط الشخص الذي استدعى الأمر يمكنه استخدام هذه القائمة.",
                ephemeral=True
            )
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        try:
            # Defer interaction first to prevent timeout
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)

            if not interaction.user.guild_permissions.administrator:
                return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)

            role_id = interaction.data["values"][0]
            if role_id == "none":
                prompt_message = await interaction.original_response()
                await prompt_message.edit(
                    content=f"{interaction.user.mention} لا توجد رتفاع للتعديل",
                    view=FeatureSelfRolesView(self.bot, self.caller_id),
                    embeds=[]
                )
                return

            # Re-use the perms view for editing
            prompt_message = await interaction.original_response()
            await prompt_message.edit(
                content=f"{interaction.user.mention} **اختر الصلاحيات الجديدة للرول**",
                view=InteractiveRolePermsView(self.bot, role_id, self.guild, self.caller_id),
                embeds=[]
            )
        except discord.HTTPException as e:
            print(f"[InteractiveRoleEditView] HTTPException in _on_select: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(f"❌ خطأ في تعديل الرول: {e}", ephemeral=True)
            except:
                pass
        except Exception as e:
            print(f"[InteractiveRoleEditView] Error in _on_select: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد الرتب التفاعلية**\nاختر إجراء للرتب التفاعلية:",
                embeds=[],
                view=FeatureSelfRolesView(self.bot, self.caller_id, self.is_shortcut)
            )
        except Exception as e:
            print(f"[InteractiveRoleEditView] Error in back_btn: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass


class CustomRoleNameView(View):
    """إنشاء رول خاص - اسم الرول (Chat Input)"""
    def __init__(self, bot_ref, guild=None, caller_id: int = None, is_shortcut: bool = False, *args, **kwargs):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.guild = guild
        self.caller_id = int(caller_id) if caller_id else None
        self.is_shortcut = is_shortcut

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "❌ فقط الشخص الذي استدعى الأمر يمكنه استخدام هذه القائمة.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="crn_back", row=0)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} اختر إجراء للرتب التفاعلية:",
                view=FeatureSelfRolesView(self.bot, self.caller_id),
                embeds=[])
        except Exception as e:
            print(f"[CustomRoleNameView] Error in back_btn: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass


class CustomRoleCancelView(View):
    """View with only Back button for chat input prompts"""
    def __init__(self, bot_ref, return_view, caller_id: int = None):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.return_view = return_view
        self.caller_id = int(caller_id) if caller_id else None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "❌ فقط الشخص الذي استدعى الأمر يمكنه استخدام هذه القائمة.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="رجوع", emoji=emojis_config.NAV_EMOJIS['back'], style=discord.ButtonStyle.secondary,
                       custom_id="crc_back", row=0)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} اختر إجراء للرتب التفاعلية:",
                view=FeatureSelfRolesView(self.bot, self.caller_id),
                embeds=[]
            )
        except Exception as e:
            print(f"[CustomRoleCancelView] Error in back_btn: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass


class CustomRoleOwnerView(View):
    """تحديد مالك الرول الخاص"""
    def __init__(self, bot_ref, guild=None, role_name=None, caller_id: int = None, is_shortcut: bool = False, *args, **kwargs):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.guild = guild
        self.role_name = role_name
        self.caller_id = int(caller_id) if caller_id else None
        self.is_shortcut = is_shortcut
        
        member_select = discord.ui.UserSelect(
            placeholder="اختر مالك الرول...",
            custom_id="cro_owner_select",
            row=0
        )
        member_select.callback = self._on_owner_select
        self.add_item(member_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.caller_id and interaction.user.id != self.caller_id:
            await interaction.response.send_message(
                "❌ فقط الشخص الذي استدعى الأمر يمكنه استخدام هذه القائمة.",
                ephemeral=True
            )
            return False
        return True

    async def _on_owner_select(self, interaction: discord.Interaction):
        try:
            # Defer immediately to prevent timeout
            await interaction.response.defer(ephemeral=True)
            
            if not interaction.user.guild_permissions.administrator:
                return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
            
            # Extract member ID from Select Menu dropdown
            owner_id = interaction.data["values"][0]
            
            # If the selected owner is the interaction user, use them directly
            if owner_id == interaction.user.id:
                target_owner = interaction.user
            else:
                # Try to get member from guild cache first
                target_owner = self.guild.get_member(owner_id)
                
                # If not in cache, try fetching from API
                if not target_owner:
                    try:
                        target_owner = await self.guild.fetch_member(owner_id)
                    except Exception:
                        pass
            
            if not target_owner:
                return await interaction.followup.send("❌ العضو غير موجود في السيرفر.", ephemeral=True)
            
            # Create the role
            try:
                role = await self.guild.create_role(
                    name=self.role_name,
                    color=discord.Color.default(),
                    mentionable=True,
                    reason=f"رول خاص لـ {target_owner.display_name}"
                )
                
                # Register the custom role in user_roles database (direct mapping)
                bd = self.bot._bot_dir
                user_roles = cfg("user_roles", bd) or {}
                
                # Direct mapping: user_id -> role_id
                user_roles[str(target_owner.id)] = str(role.id)
                set_cfg("user_roles", user_roles, bd)
                
                # Also store role metadata for reference
                custom_roles = cfg("custom_roles", bd) or {}
                custom_roles[str(role.id)] = {
                    "owner_id": target_owner.id,
                    "name": self.role_name
                }
                set_cfg("custom_roles", custom_roles, bd)
                
                # Assign the role to the target owner
                await target_owner.add_roles(role, reason="تلقائي: إنشاء رول خاص")
                
                # Show clean success message with only back button
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} تم إنشاء الرول الخاص بنجاح!\nالرول: {role.mention}\nالمالك: {target_owner.mention}",
                    view=CustomRoleCancelView(self.bot, FeatureSelfRolesView(self.bot, self.caller_id, self.is_shortcut), self.caller_id),
                    embeds=[]
                )
            except Exception as e:
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} ❌ خطأ في إنشاء الرول: {e}",
                    view=CustomRoleCancelView(self.bot, FeatureSelfRolesView(self.bot, self.caller_id, self.is_shortcut), self.caller_id),
                    embeds=[]
                )
        except Exception as e:
            print(f"[CustomRoleOwnerView] Error in _on_owner_select: {e}")
            try:
                await interaction.response.send_message(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="cro_back", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إنشاء رول خاص**\nاكتب اسم الرول:",
                view=CustomRoleNameView(self.bot, self.guild, self.caller_id),
                embeds=[])
        except Exception as e:
            print(f"[CustomRoleOwnerView] Error in back_btn: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass


async def _get_role_name_from_chat(bot_ref, interaction, prompt: str, return_view_class, *view_args):
    """Helper to get role name from chat"""
    try:
        return_view = return_view_class(bot_ref, *view_args)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} {prompt}",
            view=CustomRoleCancelView(bot_ref, return_view),
            embeds=[]
        )
        
        # Get the message object for later edits
        prompt_message = await interaction.original_response()
        
        # Wait for user's next message
        def check(msg):
            return msg.author.id == interaction.user.id and msg.channel.id == interaction.channel.id
        
        try:
            msg = await bot_ref.wait_for('message', check=check, timeout=60)
            role_name = msg.content.strip()
            
            # Delete the user's chat message to keep channel clean
            try:
                await msg.delete()
            except Exception:
                pass
            
            if not role_name:
                await prompt_message.edit(
                    content=f"{interaction.user.mention} ❌ يجب إدخال اسم الرول.",
                    view=return_view,
                    embeds=[]
                )
                return None
            
            return role_name
        except asyncio.TimeoutError:
            await prompt_message.edit(
                content=f"{interaction.user.mention} انتهى الوقت. حاول مرة أخرى.",
                view=return_view,
                embeds=[]
            )
            return None
    except Exception as e:
        print(f"[_get_role_name_from_chat] Error: {e}")
        try:
            await interaction.response.send_message(f"❌ حدث خطأ: {e}", ephemeral=True)
        except:
            pass
        return None


async def _get_auto_response_from_chat(bot_ref, interaction, prompt: str, return_view_class, caller_id: int = None):
    """Helper to get auto-response keyword and response from chat"""
    try:
        return_view = return_view_class(bot_ref, caller_id)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} {prompt}",
            view=CustomRoleCancelView(bot_ref, return_view, caller_id),
            embeds=[]
        )

        # Get the message object for later edits
        prompt_message = await interaction.original_response()

        # Wait for user's next message (keyword)
        def check(msg):
            return msg.author.id == interaction.user.id and msg.channel.id == interaction.channel.id

        try:
            # Get keyword
            msg = await bot_ref.wait_for('message', check=check, timeout=60)
            keyword = msg.content.strip()

            # Delete the user's chat message to keep channel clean
            try:
                await msg.delete()
            except Exception:
                pass

            if not keyword:
                await prompt_message.edit(
                    content=f"{interaction.user.mention} ❌ يجب إدخال الكلمة المفتاحية.",
                    view=return_view,
                    embeds=[]
                )
                return None, None

            # Prompt for response
            await prompt_message.edit(
                content=f"{interaction.user.mention} اكتب الرد التلقائي في الشات الآن:",
                view=CustomRoleCancelView(bot_ref, return_view, caller_id),
                embeds=[]
            )

            # Get response
            msg2 = await bot_ref.wait_for('message', check=check, timeout=60)
            response = msg2.content.strip()

            # Delete the user's chat message to keep channel clean
            try:
                await msg2.delete()
            except Exception:
                pass

            if not response:
                await prompt_message.edit(
                    content=f"{interaction.user.mention} ❌ يجب إدخال الرد التلقائي.",
                    view=return_view,
                    embeds=[]
                )
                return None, None

            return keyword, response

        except asyncio.TimeoutError:
            await prompt_message.edit(
                content=f"{interaction.user.mention} انتهى الوقت. حاول مرة أخرى.",
                view=return_view,
                embeds=[]
            )
            return None, None
    except Exception as e:
        print(f"[_get_auto_response_from_chat] Error: {e}")
        return None, None


class CustomRoleControlView(View):
    """لوحة تحكم الرول الخاص للمالك"""
    def __init__(self, bot_ref, guild=None, role=None, owner=None, *args, **kwargs):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.guild = guild
        self.role = role
        self.owner = owner

        # Get emojis from config
        try:
            emoji_add_member = emojis_config.ROLE_CMD_EMOJIS["add_member"]
            emoji_remove_member = emojis_config.ROLE_CMD_EMOJIS["remove_member"]
            emoji_change_name = emojis_config.ROLE_CMD_EMOJIS["change_name"]
            emoji_change_color = emojis_config.ROLE_CMD_EMOJIS["change_color"]
            emoji_toggle_mention = emojis_config.ROLE_CMD_EMOJIS["toggle_mention"]
            emoji_add_icon = emojis_config.ROLE_CMD_EMOJIS["add_icon"]
        except Exception:
            emoji_add_member = None
            emoji_remove_member = None
            emoji_change_name = None
            emoji_change_color = None
            emoji_toggle_mention = None
            emoji_add_icon = None

        options = [
            discord.SelectOption(label="إضافة شخص للرول", value="add_member", description="إضافة عضو للرول", emoji=emoji_add_member),
            discord.SelectOption(label="إزالة شخص من الرول", value="remove_member", description="إزالة عضو من الرول", emoji=emoji_remove_member),
            discord.SelectOption(label="تغيير اسم الرول", value="rename", description="تغيير اسم الرول", emoji=emoji_change_name),
            discord.SelectOption(label="تغيير لون الرول", value="color", description="تغيير لون الرول", emoji=emoji_change_color),
            discord.SelectOption(label="تفعيل/إغلاق المنشن", value="mentionable", description="تفعيل أو إغلاق المنشن", emoji=emoji_toggle_mention),
            discord.SelectOption(label="إضافة ملصق للرول", value="icon", description="إضافة ملصق للرول", emoji=emoji_add_icon),
        ]

        select = discord.ui.Select(
            placeholder="اختر إجراء...",
            options=options,
            custom_id="crc_select",
            row=0
        )
        select.callback = self._on_select
        self.add_item(select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(
                "❌ فقط الشخص الذي استدعى الأمر يمكنه استخدام هذه القائمة.",
                ephemeral=True
            )
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        try:
            if interaction.user.id != self.owner.id:
                return await interaction.response.send_message("⛔ هذا للمالك فقط.", ephemeral=True)

            choice = interaction.data["values"][0]

            if choice == "add_member":
                await interaction.response.defer(ephemeral=True)
                await interaction.message.edit(
                    content=f"{interaction.user.mention} **إضافة شخص للرول**\nمنشن الشخص:",
                    view=CustomRoleAddMemberView(self.bot, self.guild, self.role, self.owner)
                )
            elif choice == "remove_member":
                await interaction.response.defer(ephemeral=True)
                await interaction.message.edit(
                    content=f"{interaction.user.mention} **إزالة شخص من الرول**\nمنشن الشخص:",
                    view=CustomRoleRemoveMemberView(self.bot, self.guild, self.role, self.owner)
                )
            elif choice == "rename":
                # Use chat listener with defer to prevent timeout
                await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(
                    "✏️ يرجى إرسال الاسم الجديد للرول في الشات خلال 30 ثانية...",
                    ephemeral=True
                )
                
                # Wait for user's message
                def check(m):
                    return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
                
                try:
                    msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                    new_name = msg.content.strip()
                    
                    # Handle cancellation
                    if new_name.lower() == 'إلغاء':
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                        await interaction.followup.send("❌ تم إلغاء العملية", ephemeral=True)
                        # Restore the view
                        await interaction.message.edit(
                            content=f"{interaction.user.mention} تعديل رولي:",
                            view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                        )
                        return
                    
                    # Delete the user's chat message to keep channel clean
                    try:
                        await msg.delete()
                    except Exception:
                        pass
                    
                    if not new_name:
                        await interaction.followup.send("❌ يجب إدخال اسم الرول.", ephemeral=True)
                        # Edit the original public message directly - NO new view in ephemeral
                        await interaction.message.edit(
                            content=f"{interaction.user.mention} تعديل رولي:",
                            view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                        )
                        return
                    
                    try:
                        await self.role.edit(name=new_name)
                        # Edit the original public message directly - NO new view in ephemeral
                        await interaction.message.edit(
                            content=f"{interaction.user.mention} تعديل رولي:\n**تم تغيير اسم الرول إلى {new_name}**",
                            view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                        )
                        await interaction.followup.send("✅ تم تغيير اسم الرول بنجاح", ephemeral=True)
                    except Exception as e:
                        await interaction.followup.send(f"❌ خطأ: {e}", ephemeral=True)
                        # Edit the original public message directly - NO new view in ephemeral
                        await interaction.message.edit(
                            content=f"{interaction.user.mention} تعديل رولي:",
                            view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                        )
                        
                except asyncio.TimeoutError:
                    await interaction.followup.send("❌ انتهت المهلة ولم تقم بإرسال الاسم.", ephemeral=True)
                    # Edit the original public message directly - NO new view in ephemeral
                    await interaction.message.edit(
                        content=f"{interaction.user.mention} تعديل رولي:",
                        view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                    )
            elif choice == "color":
                # Send modal directly without defer - webhooks don't support send_modal
                await interaction.response.send_modal(CustomRoleColorModal(self.bot, self.guild, self.role, self.owner))
            elif choice == "mentionable":
                # Defer first, then toggle, no double defer in _toggle_mentionable
                await interaction.response.defer(ephemeral=True)
                try:
                    await self.role.edit(mentionable=not self.role.mentionable)
                    status = "مُفعَّل" if self.role.mentionable else "مُعطَّل"
                    # Edit the original public message directly - NO new view in ephemeral
                    await interaction.message.edit(
                        content=f"{interaction.user.mention} تعديل رولي:\n**المنشن الآن {status}**",
                        view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                    )
                    await interaction.followup.send(f"✅ تم تغيير حالة المنشن", ephemeral=True)
                except Exception as e:
                    print(f"[CustomRoleControlView] Error in mentionable toggle: {e}")
                    try:
                        await interaction.followup.send(f"❌ خطأ: {e}", ephemeral=True)
                    except:
                        pass
            elif choice == "icon":
                # Use chat listener instead of modal - NO VIEW in ephemeral response
                await interaction.response.send_message(
                    "📌 يرجى إرسال الإيموجي أو رابط الصورة في الشات خلال 30 ثانية...",
                    ephemeral=True
                )
                
                # Wait for user's message
                def check(m):
                    return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
                
                try:
                    msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                    icon_input = msg.content.strip()
                    
                    # Delete the user's chat message to keep channel clean
                    try:
                        await msg.delete()
                    except Exception:
                        pass
                    
                    # Check guild boost tier before attempting to set icon
                    if self.guild.premium_tier < 2:
                        await interaction.followup.send(
                            "⚠️ السيرفر يحتاج إلى Level 2 Boost (6 بوستات) لاستخدام خاصية أيقونات الرولات.",
                            ephemeral=True
                        )
                        # Edit the original public message directly - NO new view in ephemeral
                        await interaction.message.edit(
                            content=f"{interaction.user.mention} تعديل رولي:",
                            view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                        )
                        return
                    
                    try:
                        # Check if input is a custom Discord emoji pattern
                        custom_emoji_pattern = r'<a?:(\w+):(\d+)>'
                        custom_emoji_match = re.search(custom_emoji_pattern, icon_input)
                        
                        if custom_emoji_match:
                            # It's a custom server emoji - construct CDN URL
                            emoji_id = custom_emoji_match.group(2)
                            # Try .gif first (animated), fallback to .png
                            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.gif"
                            
                            if 'aiohttp' not in globals():
                                await interaction.followup.send(
                                    "❌ مكتبة aiohttp غير متوفرة لتحميل الصور.",
                                    ephemeral=True
                                )
                                # Edit the original public message directly - NO new view in ephemeral
                                await interaction.message.edit(
                                    content=f"{interaction.user.mention} تعديل رولي:",
                                    view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                                )
                                return
                            
                            async with aiohttp.ClientSession() as session:
                                async with session.get(emoji_url) as resp:
                                    if resp.status == 200:
                                        image_bytes = await resp.read()
                                        await self.role.edit(display_icon=image_bytes)
                                    else:
                                        # Try .png as fallback
                                        emoji_url_png = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
                                        async with session.get(emoji_url_png) as resp_png:
                                            if resp_png.status == 200:
                                                image_bytes = await resp_png.read()
                                                await self.role.edit(display_icon=image_bytes)
                                            else:
                                                await interaction.followup.send(
                                                    "❌ فشل تحميل الإيموجي المخصص.",
                                                    ephemeral=True
                                                )
                                                # Edit the original public message directly - NO new view in ephemeral
                                                await interaction.message.edit(
                                                    content=f"{interaction.user.mention} تعديل رولي:",
                                                    view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                                                )
                                                return
                        elif icon_input.startswith("http"):
                            # It's a URL - fetch the image
                            if 'aiohttp' not in globals():
                                await interaction.followup.send(
                                    "❌ مكتبة aiohttp غير متوفرة لتحميل الصور من الروابط.",
                                    ephemeral=True
                                )
                                # Edit the original public message directly - NO new view in ephemeral
                                await interaction.message.edit(
                                    content=f"{interaction.user.mention} تعديل رولي:",
                                    view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                                )
                                return
                            
                            async with aiohttp.ClientSession() as session:
                                async with session.get(icon_input) as resp:
                                    if resp.status == 200:
                                        image_bytes = await resp.read()
                                        await self.role.edit(display_icon=image_bytes)
                                    else:
                                        await interaction.followup.send(
                                            "❌ فشل تحميل الصورة. تأكد من صحة الرابط.",
                                            ephemeral=True
                                        )
                                        # Edit the original public message directly - NO new view in ephemeral
                                        await interaction.message.edit(
                                            content=f"{interaction.user.mention} تعديل رولي:",
                                            view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                                        )
                                        return
                        else:
                            # It's a unicode emoji - try to use it directly
                            try:
                                # Discord accepts unicode emojis directly
                                await self.role.edit(display_icon=icon_input)
                            except Exception:
                                await interaction.followup.send(
                                    "❌ الإيموجي غير صالح. استخدم إيموجي يونيكود عادي أو رابط صورة أو إيموجي سيرفر.",
                                    ephemeral=True
                                )
                                # Edit the original public message directly - NO new view in ephemeral
                                await interaction.message.edit(
                                    content=f"{interaction.user.mention} تعديل رولي:",
                                    view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                                )
                                return
                        
                        # Success - edit the original public message directly - NO new view in ephemeral
                        await interaction.message.edit(
                            content=f"{interaction.user.mention} تعديل رولي:\n**تم تغيير أيقونة الرول بنجاح**",
                            view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                        )
                        await interaction.followup.send(
                            "✅ تم تطبيق الأيقونة بنجاح",
                            ephemeral=True
                        )
                        
                    except discord.Forbidden:
                        await interaction.followup.send(
                            "❌ لا صلاحية لتعديل الأيقونة. تأكد من أن رتبة البوت أعلى من الرول.",
                            ephemeral=True
                        )
                        # Edit the original public message directly - NO new view in ephemeral
                        await interaction.message.edit(
                            content=f"{interaction.user.mention} تعديل رولي:",
                            view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                        )
                    except discord.HTTPException as e:
                        if "premium" in str(e).lower() or "boost" in str(e).lower():
                            await interaction.followup.send(
                                "⚠️ السيرفر يحتاج إلى Level 2 Boost (6 بوستات) لاستخدام خاصية أيقونات الرولات.",
                                ephemeral=True
                            )
                        else:
                            await interaction.followup.send(
                                f"❌ خطأ في تعديل الأيقونة: {e}",
                                ephemeral=True
                            )
                        # Edit the original public message directly - NO new view in ephemeral
                        await interaction.message.edit(
                            content=f"{interaction.user.mention} تعديل رولي:",
                            view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                        )
                    except Exception as e:
                        await interaction.followup.send(f"❌ خطأ: {e}", ephemeral=True)
                        # Edit the original public message directly - NO new view in ephemeral
                        await interaction.message.edit(
                            content=f"{interaction.user.mention} تعديل رولي:",
                            view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                        )
                        
                except asyncio.TimeoutError:
                    await interaction.followup.send("❌ انتهت المهلة ولم تقم بإرسال المطلوب.", ephemeral=True)
                    # Edit the original public message directly - NO new view in ephemeral
                    await interaction.message.edit(
                        content=f"{interaction.user.mention} تعديل رولي:",
                        view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                    )
                    
        except Exception as e:
            print(f"[CustomRoleControlView] Error in _on_select: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass


class CustomRoleAddMemberView(View):
    """إضافة عضو للرول الخاص"""
    def __init__(self, bot_ref, guild, role, owner, *args, **kwargs):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.guild = guild
        self.role = role
        self.owner = owner
        
        member_select = discord.ui.UserSelect(
            placeholder="اختر العضو...",
            custom_id="cram_select",
            row=0
        )
        member_select.callback = self._on_select
        self.add_item(member_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(
                "❌ فقط الشخص الذي استدعى الأمر يمكنه استخدام هذه القائمة.",
                ephemeral=True
            )
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        try:
            # Defer interaction first to prevent timeout
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            
            if interaction.user.id != self.owner.id:
                return await interaction.followup.send("⛔ هذا للمالك فقط.", ephemeral=True)
            
            # Extract member ID safely
            member_id = interaction.data["values"][0]
            
            # Get member with fallback
            member = self.guild.get_member(member_id)
            if not member:
                try:
                    member = await self.guild.fetch_member(member_id)
                except Exception:
                    pass
            
            if member:
                await member.add_roles(self.role, reason=f"إضافة للرول الخاص بواسطة {self.owner.display_name}")
                
                # Edit the original public message directly - NO new view in ephemeral
                await interaction.message.edit(
                    content=f"{interaction.user.mention} تعديل رولي:\n**تم إضافة {member.mention} للرول**",
                    view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                )
                await interaction.followup.send("✅ تم إضافة العضو للرول", ephemeral=True)
            else:
                await interaction.followup.send("❌ العضو غير موجود في السيرفر.", ephemeral=True)
        except Exception as e:
            print(f"[CustomRoleAddMemberView] Error in _on_select: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="cram_back", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        try:
            # Edit the original public message directly - NO new view in ephemeral
            await interaction.message.edit(
                content=f"{interaction.user.mention} تعديل رولي:",
                view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
            )
        except Exception as e:
            print(f"[CustomRoleAddMemberView] Error in back_btn: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass


class CustomRoleRemoveMemberView(View):
    """إزالة عضو من الرول الخاص"""
    def __init__(self, bot_ref, guild, role, owner, *args, **kwargs):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.guild = guild
        self.role = role
        self.owner = owner
        
        member_select = discord.ui.UserSelect(
            placeholder="اختر العضو...",
            custom_id="crrm_select",
            row=0
        )
        member_select.callback = self._on_select
        self.add_item(member_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(
                "❌ فقط الشخص الذي استدعى الأمر يمكنه استخدام هذه القائمة.",
                ephemeral=True
            )
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        try:
            # Defer interaction first to prevent timeout
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            
            # Extract member ID safely
            member_id = interaction.data["values"][0]
            
            # Get member with fallback
            member = self.guild.get_member(member_id)
            if not member:
                try:
                    member = await self.guild.fetch_member(member_id)
                except Exception:
                    pass
            
            if member:
                await member.remove_roles(self.role, reason=f"إزالة من الرول الخاص بواسطة {self.owner.display_name}")
                
                # Edit the original public message directly - NO new view in ephemeral
                await interaction.message.edit(
                    content=f"{interaction.user.mention} تعديل رولي:\n**تم إزالة {member.mention} من الرول**",
                    view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
                )
                await interaction.followup.send("✅ تم إزالة العضو من الرول", ephemeral=True)
            else:
                await interaction.followup.send("❌ العضو غير موجود في السيرفر.", ephemeral=True)
        except Exception as e:
            print(f"[CustomRoleRemoveMemberView] Error in _on_select: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="crrm_back", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        try:
            # Edit the original public message directly - NO new view in ephemeral
            await interaction.message.edit(
                content=f"{interaction.user.mention} تعديل رولي:",
                view=CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
            )
        except Exception as e:
            print(f"[CustomRoleRemoveMemberView] Error in back_btn: {e}")
            try:
                await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)
            except:
                pass


class CustomRoleColorModal(Modal, title="تغيير لون الرول"):
    color_field = TextInput(label="كود اللون (Hex)", placeholder="مثال: #FF5733", max_length=7)
    
    def __init__(self, bot_ref, guild, role, owner):
        super().__init__()
        self.bot = bot_ref
        self.guild = guild
        self.role = role
        self.owner = owner
    
    async def on_submit(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        if interaction.user.id != self.owner.id:
            return await interaction.followup.send("⛔ هذا للمالك فقط.", ephemeral=True)
        
        color_hex = self.color_field.value.strip()
        if not color_hex.startswith("#"):
            color_hex = "#" + color_hex
        
        try:
            color = discord.Color(int(color_hex[1:], 16))
            await self.role.edit(color=color)
            # Create fresh view to ensure select menu is reset
            fresh_view = CustomRoleControlView(self.bot, self.guild, self.role, self.owner)
            # Edit the original public message directly - NO new view in ephemeral
            await interaction.message.edit(
                content=f"{interaction.user.mention} تعديل رولي:\n**تم تغيير لون الرول إلى {color_hex}**",
                view=fresh_view
            )
            await interaction.followup.send("✅ تم تغيير لون الرول بنجاح", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {e}", ephemeral=True)


class SelfRoleAddPickView(View):
    """اختيار الرتبة لإضافتها للنظام"""
    def __init__(self, bot_ref, options: list, caller_id: int = None):
        super().__init__(timeout=60)
        self.bot = bot_ref
        self.caller_id = int(caller_id) if caller_id else None
        sel = discord.ui.Select(
            placeholder="اختر الرتبة...", options=options,
            custom_id="srap_sel_v6", row=0)
        sel.callback = self._on_select
        self.add_item(sel)

    async def _on_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        role_id = int(interaction.data["values"][0])
        role    = interaction.guild.get_role(role_id)
        # عرض Modal لإدخال اللاصقة والإيموجي
        await interaction.followup.send_modal(
            SelfRoleConfigModal(self.bot, role_id,
                                role.name[:50] if role else str(role_id), self.caller_id))

    @discord.ui.button(label="🔙  رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="srap_back_v6", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            embed=_feature_selfroles_embed(self.bot, interaction.guild),
            view=FeatureSelfRolesView(self.bot, self.caller_id))


class SelfRoleConfigModal(Modal, title="⚙️ إعداد الرتبة التفاعلية"):
    label_field = TextInput(label="نص الزر (Label)", placeholder="مثال: 🎮 عشاق الألعاب", max_length=50)
    emoji_field = TextInput(label="إيموجي الزر (اختياري)", placeholder="🎭", required=False, max_length=5)
    desc_field  = TextInput(label="وصف الرتبة (اختياري)", placeholder="رتبة لعشاق الألعاب...",
                             required=False, max_length=100, style=discord.TextStyle.short)

    def __init__(self, bot_ref, role_id: int, default_label: str, caller_id: int = None):
        super().__init__()
        self.bot     = bot_ref
        self.role_id = role_id
        self.caller_id = int(caller_id) if caller_id else None
        self.label_field.default = default_label

    async def on_submit(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        bd      = self.bot._bot_dir
        sr_cfg  = _get_self_roles_config(bd)
        label   = self.label_field.value.strip() or f"رتبة {self.role_id}"
        emoji   = self.emoji_field.value.strip() or "🎭"
        desc    = self.desc_field.value.strip()
        sr_cfg[str(self.role_id)] = {"label": label, "emoji": emoji, "description": desc}
        set_cfg("self_roles_config", sr_cfg, bd)
        role = interaction.guild.get_role(self.role_id)
        await interaction.edit_original_response(
            embed=_feature_selfroles_embed(self.bot, interaction.guild),
            view=FeatureSelfRolesView(self.bot, self.caller_id))
        await interaction.followup.send(
            embed=_embed("✅ تمت الإضافة",
                         f"الرتبة {role.mention if role else self.role_id} أُضيفت بنجاح.\n"
                         f"الزر: {emoji} **{label}**", C.SUCCESS),
            ephemeral=True)


class SelfRoleDeleteView(View):
    def __init__(self, bot_ref, options: list, caller_id: int = None):
        super().__init__(timeout=60)
        self.bot = bot_ref
        self.caller_id = int(caller_id) if caller_id else None
        sel = discord.ui.Select(
            placeholder="اختر الرتبة للحذف...", options=options,
            custom_id="srdel_sel_v6", row=0)
        sel.callback = self._on_select
        self.add_item(sel)

    async def _on_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        rid_str = interaction.data["values"][0]
        bd      = self.bot._bot_dir
        sr_cfg  = _get_self_roles_config(bd)
        sr_cfg.pop(rid_str, None)
        set_cfg("self_roles_config", sr_cfg, bd)
        await interaction.edit_original_response(
            embed=_feature_selfroles_embed(self.bot, interaction.guild),
            view=FeatureSelfRolesView(self.bot, self.caller_id))
        await interaction.followup.send(
            embed=_embed("✅ تم الحذف", f"تم حذف الرتبة `{rid_str}` من النظام.", C.SUCCESS),
            ephemeral=True)

    @discord.ui.button(label="🔙  رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="srdel_back_v6", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            embed=_feature_selfroles_embed(self.bot, interaction.guild),
            view=FeatureSelfRolesView(self.bot, self.caller_id))


class SelfRolesPanel(View):
    """
    لوحة الرتب التفاعلية التي تُنشر للأعضاء.
    كل رتبة = زر. الضغط يعطي أو يسلب الرتبة.
    """
    def __init__(self, bot_ref, sr_cfg: dict):
        super().__init__(timeout=None)
        self.bot = bot_ref
        for rid_str, rdata in list(sr_cfg.items())[:25]:
            label   = rdata.get("label", f"رتبة {rid_str}")[:80]
            emoji_s = rdata.get("emoji", "🎭")
            btn = Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                custom_id=f"self_role_{rid_str}_v6",
                emoji=emoji_s if len(emoji_s) <= 2 else None)
            btn.callback = self._make_callback(int(rid_str))
            self.add_item(btn)

    def _make_callback(self, role_id: int):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            guild  = interaction.guild
            member = interaction.user
            if not bool(cfg("feature_self_roles", self.bot._bot_dir)):
                return await interaction.followup.send(
                    embed=_embed("⚠️ معطّل", "نظام الرتب التفاعلية غير مُفعَّل.", C.WARNING),
                    ephemeral=True)
            role = guild.get_role(role_id)
            if not role:
                return await interaction.followup.send(
                    embed=_embed("❌ خطأ", "الرتبة غير موجودة.", C.DANGER), ephemeral=True)
            
            # Active Sanction Roles Verification - Prevent role conflicts
            bd = self.bot._bot_dir
            mute_role_id = cfg("mute_role", bd)
            jail_role_id = cfg("jail_role_id", bd)
            
            # Check if member has active jail or mute role
            has_active_sanction = False
            if mute_role_id and any(r.id == int(mute_role_id) for r in member.roles):
                has_active_sanction = True
            if jail_role_id and any(r.id == int(jail_role_id) for r in member.roles):
                has_active_sanction = True
            
            if role in member.roles:
                await member.remove_roles(role, reason="Self-Role إلغاء")
                await interaction.followup.send(
                    embed=_embed("🎭 تم الإلغاء", f"تم إزالة رتبة {role.mention} منك.", C.WARNING),
                    ephemeral=True)
            else:
                if has_active_sanction:
                    return await interaction.followup.send(
                        embed=_embed("⛔ محظور", "لا يمكنك الحصول على رتب تفاعلية أثناء وجود عقوبة نشطة.", C.DANGER),
                        ephemeral=True)
                await member.add_roles(role, reason="Self-Role اختيار")
                await interaction.followup.send(
                    embed=_embed("✅ تم الحصول", f"حصلت على رتبة {role.mention} 🎉", C.SUCCESS),
                    ephemeral=True)
        return callback


# ────────────────────────────────────────────────────────────────────────────
# 8️⃣  الرد التلقائي (Auto-Response) — ميزة جديدة v7.0
# ────────────────────────────────────────────────────────────────────────────
def _get_auto_responses(bot_dir=None) -> dict:
    """يرجع dict: {"keyword": "reply_text"}"""
    data = cfg("auto_responses", bot_dir)
    if isinstance(data, dict):
        return data
    return {}


def _feature_autoresp_embed(bot_ref, guild: discord.Guild) -> discord.Embed:
    bd      = bot_ref._bot_dir
    ar_data = _get_auto_responses(bd)
    lines   = []
    for kw, rp in list(ar_data.items())[:15]:
        lines.append(f"🔑 `{kw[:30]}` → `{rp[:50]}`")
    resp_text = "\n".join(lines) if lines else "⬜ لا توجد ردود مُضافة بعد"
    return _embed(
        "💬  إعداد الرد التلقائي",
        f"**الحالة:** 🟢 مُفعَّل دائماً\n"
        f"**عدد الردود:** `{len(ar_data)}`\n"
        f"{_sep()}"
        f"**الردود الحالية:**\n{resp_text}\n"
        f"{_sep()}"
        "أضف كلمة مفتاحية وردًا لها، أو احذف رداً موجوداً.",
        C.INFO,
        footer="System Bot  •  💬 الرد التلقائي  •  v7.0"
    )


# ════════════════════════════════════════════════════════════════════════════
class FeatureAutoResponseView(View):
    """واجهة إعداد الرد التلقائي"""
    def __init__(self, bot_ref, caller_id: int = None):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.caller_id = int(caller_id) if caller_id else None

        menu_options = [
            discord.SelectOption(label="إضافة رد تلقائي", value="add", description="إضافة رد تلقائي جديد", emoji=emojis_config.AUTO_RESPONSE_EMOJIS.get("add", "➕")),
            discord.SelectOption(label="إزالة رد تلقائي", value="delete", description="حذف رد تلقائي موجود", emoji=emojis_config.AUTO_RESPONSE_EMOJIS.get("delete", "🗑️")),
            discord.SelectOption(label="تعديل رد تلقائي", value="edit", description="تعديل رد تلقائي موجود", emoji=emojis_config.AUTO_RESPONSE_EMOJIS.get("edit", "✏️")),
        ]

        menu = discord.ui.Select(
            placeholder="اختر إجراء للردود التلقائية...",
            options=menu_options,
            custom_id="auto_resp_menu",
            row=0
        )
        menu.callback = self._on_menu_select
        self.add_item(menu)

        # Back button
        back_btn = discord.ui.Button(label="🔙 رجوع للقائمة", style=discord.ButtonStyle.secondary,
                                     custom_id="auto_resp_back_btn", row=1, emoji=emojis_config.AUTO_RESPONSE_EMOJIS.get("back", "🔙"))
        back_btn.callback = self.back_btn
        self.add_item(back_btn)

    async def _on_menu_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)

        choice = interaction.data["values"][0]

        if choice == "add":
            # Start chat input for keyword and response
            keyword, response = await _get_auto_response_from_chat(
                self.bot,
                interaction,
                "اكتب الكلمة المفتاحية في الشات الآن:",
                FeatureAutoResponseView,
                self.caller_id
            )
            if keyword and response:
                # Save to database
                bd = self.bot._bot_dir
                ar_data = _get_auto_responses(bd)
                ar_data[keyword.lower()] = response
                set_cfg("auto_responses", ar_data, bd)

                # Return to main menu
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **إعداد الردود التلقائية**\nاختر إجراء للردود التلقائية:",
                    embeds=[],
                    view=FeatureAutoResponseView(self.bot, self.caller_id)
                )
                await interaction.followup.send(
                    embed=_embed("✅ تمت الإضافة",
                                 f"🔑 الكلمة: `{keyword}`\n💬 الرد: `{response[:80]}`", C.SUCCESS),
                    ephemeral=True)
        elif choice == "delete":
            ar_data = _get_auto_responses(self.bot._bot_dir)
            if not ar_data:
                return await interaction.followup.send(
                    embed=_embed("⚠️", "لا توجد ردود لحذفها.", C.WARNING), ephemeral=True)
            options = [
                discord.SelectOption(label=kw[:50], value=kw, description=rp[:80])
                for kw, rp in list(ar_data.items())[:25]
            ]
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **حذف رد تلقائي**\nاختر الكلمة المفتاحية للحذف:",
                embeds=[],
                view=AutoResponseDeleteView(self.bot, options, self.caller_id))
        elif choice == "edit":
            ar_data = _get_auto_responses(self.bot._bot_dir)
            if not ar_data:
                return await interaction.followup.send(
                    embed=_embed("⚠️", "لا توجد ردود للتعديل.", C.WARNING), ephemeral=True)
            options = [
                discord.SelectOption(label=kw[:50], value=kw, description=rp[:80])
                for kw, rp in list(ar_data.items())[:25]
            ]
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **تعديل رد تلقائي**\nاختر الكلمة المفتاحية للتعديل:",
                embeds=[],
                view=AutoRespEditPickView(self.bot, options, self.caller_id))

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
            embeds=[],
            view=Step3SettingsView(self.bot, self.caller_id))





class AutoResponseDeleteView(View):
    def __init__(self, bot_ref, options: list, caller_id: int = None):
        super().__init__(timeout=60)
        self.bot = bot_ref
        self.caller_id = int(caller_id) if caller_id else None
        sel = discord.ui.Select(placeholder="اختر الكلمة للحذف...",
                                options=options, custom_id="auto_resp_del_sel", row=0)
        sel.callback = self._on_select
        self.add_item(sel)

        # Back button
        back_btn = discord.ui.Button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                                     custom_id="auto_resp_del_back", row=1, emoji=emojis_config.AUTO_RESPONSE_EMOJIS.get("back", "🔙"))
        back_btn.callback = self.back_btn
        self.add_item(back_btn)

    async def _on_select(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)

        kw      = interaction.data["values"][0]
        bd      = self.bot._bot_dir
        ar_data = _get_auto_responses(bd)
        ar_data.pop(kw, None)
        set_cfg("auto_responses", ar_data, bd)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **إعداد الردود التلقائية**\nاختر إجراء للردود التلقائية:",
            embeds=[],
            view=FeatureAutoResponseView(self.bot, self.caller_id))
        await interaction.followup.send(
            embed=_embed("✅ تم الحذف", f"حُذف الرد للكلمة `{kw}`.", C.SUCCESS),
            ephemeral=True)

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **إعداد الردود التلقائية**\nاختر إجراء للردود التلقائية:",
            embeds=[],
            view=FeatureAutoResponseView(self.bot, self.caller_id))


class AutoRespEditPickView(View):
    """اختيار رد تلقائي للتعديل"""
    def __init__(self, bot_ref, options: list, caller_id: int = None):
        super().__init__(timeout=60)
        self.bot = bot_ref
        self.caller_id = int(caller_id) if caller_id else None
        sel = discord.ui.Select(placeholder="اختر الكلمة للتعديل...",
                                options=options, custom_id="auto_resp_edit_sel", row=0)
        sel.callback = self._on_select
        self.add_item(sel)

        # Back button
        back_btn = discord.ui.Button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                                     custom_id="auto_resp_edit_back", row=1, emoji=emojis_config.AUTO_RESPONSE_EMOJIS.get("back", "🔙"))
        back_btn.callback = self.back_btn
        self.add_item(back_btn)

    async def _on_select(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)

        kw = interaction.data["values"][0]
        # Show the edit options menu instead of modal
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **تعديل رد تلقائي**\nالكلمة المختارة: `{kw}`\nاختر ما تريد تعديله:",
            embeds=[],
            view=AutoRespEditOptionsView(self.bot, kw, self.caller_id))

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **إعداد الردود التلقائية**\nاختر إجراء للردود التلقائية:",
            embeds=[],
            view=FeatureAutoResponseView(self.bot, self.caller_id))


class AutoRespEditOptionsView(View):
    """خيارات تعديل الرد التلقائي: الكلمة المفتاحية أو النص"""
    def __init__(self, bot_ref, keyword: str, caller_id: int = None):
        super().__init__(timeout=60)
        self.bot = bot_ref
        self.keyword = keyword
        self.caller_id = int(caller_id) if caller_id else None

        menu_options = [
            discord.SelectOption(label="تعديل الكلمة المفتاحية", value="edit_keyword", 
                               description="تغيير الكلمة التي تُطلق الرد التلقائي", 
                               emoji=emojis_config.AUTO_RESPONSE_EMOJIS.get("edit_keyword", "✏️")),
            discord.SelectOption(label="تعديل النص / الرد", value="edit_response", 
                               description="تغيير نص الرد التلقائي", 
                               emoji=emojis_config.AUTO_RESPONSE_EMOJIS.get("edit_response", "✏️")),
        ]

        menu = discord.ui.Select(
            placeholder="اختر نوع التعديل...",
            options=menu_options,
            custom_id="auto_resp_edit_options",
            row=0
        )
        menu.callback = self._on_menu_select
        self.add_item(menu)

        # Back button to return to keyword selection
        back_btn = discord.ui.Button(label="🔙 رجوع", style=discord.ButtonStyle.secondary,
                                     custom_id="auto_resp_edit_options_back", row=1, 
                                     emoji=emojis_config.AUTO_RESPONSE_EMOJIS.get("back", "🔙"))
        back_btn.callback = self.back_btn
        self.add_item(back_btn)

    async def _on_menu_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        choice = interaction.data["values"][0]

        if choice == "edit_keyword":
            # Prompt for new keyword via chat
            await self._edit_keyword_workflow(interaction)
        elif choice == "edit_response":
            # Prompt for new response via chat
            await self._edit_response_workflow(interaction)

    async def _edit_keyword_workflow(self, interaction: discord.Interaction):
        """Workflow for editing the keyword via chat input"""
        # Get the message object for later edits
        prompt_message = await interaction.original_response()

        # Show prompt in the message
        await prompt_message.edit(
            content=f"{interaction.user.mention} **تعديل الكلمة المفتاحية**\n"
                    f"الكلمة الحالية: `{self.keyword}`\n\n"
                    f"أرسل الكلمة المفتاحية الجديدة في الشات (أو اكتب 'إلغاء' للإلغاء):",
            view=AutoRespEditCancelView(self.bot, self.keyword, self.caller_id, "keyword"),
            embeds=[]
        )

        # Wait for user's next message
        def check(msg):
            return msg.author.id == interaction.user.id and msg.channel.id == interaction.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            new_keyword = msg.content.strip()

            # Delete the user's chat message to keep channel clean
            try:
                await msg.delete()
            except Exception:
                pass

            # Check for cancellation
            if new_keyword.lower() == "إلغاء":
                await prompt_message.edit(
                    content=f"{interaction.user.mention} **تم إلغاء العملية**",
                    view=FeatureAutoResponseView(self.bot, self.caller_id),
                    embeds=[]
                )
                return

            if not new_keyword:
                await prompt_message.edit(
                    content=f"{interaction.user.mention} ❌ يجب إدخال كلمة مفتاحية صالحة.",
                    view=AutoRespEditOptionsView(self.bot, self.keyword, self.caller_id),
                    embeds=[]
                )
                return

            # Update the keyword in database
            bd = self.bot._bot_dir
            ar_data = _get_auto_responses(bd)
            
            # Get the current response
            current_response = ar_data.get(self.keyword, "")
            
            # Remove old keyword and add new one with same response
            ar_data.pop(self.keyword, None)
            ar_data[new_keyword.lower()] = current_response
            set_cfg("auto_responses", ar_data, bd)

            # Return to main menu with success message
            await prompt_message.edit(
                content=f"{interaction.user.mention} **إعداد الردود التلقائية**\nاختر إجراء للردود التلقائية:",
                view=FeatureAutoResponseView(self.bot, self.caller_id),
                embeds=[]
            )
            await interaction.followup.send(
                embed=_embed("✅ تم تعديل الكلمة المفتاحية بنجاح!",
                             f"🔑 الكلمة القديمة: `{self.keyword}`\n"
                             f"🔑 الكلمة الجديدة: `{new_keyword}`", C.SUCCESS),
                ephemeral=True)

        except asyncio.TimeoutError:
            await prompt_message.edit(
                content=f"{interaction.user.mention} انتهى الوقت. حاول مرة أخرى.",
                view=FeatureAutoResponseView(self.bot, self.caller_id),
                embeds=[]
            )

    async def _edit_response_workflow(self, interaction: discord.Interaction):
        """Workflow for editing the response text via chat input"""
        # Get the message object for later edits
        prompt_message = await interaction.original_response()

        # Show prompt in the message
        await prompt_message.edit(
            content=f"{interaction.user.mention} **تعديل النص / الرد**\n"
                    f"الكلمة المفتاحية: `{self.keyword}`\n\n"
                    f"أرسل الرد التلقائي الجديد في الشات (أو اكتب 'إلغاء' للإلغاء):",
            view=AutoRespEditCancelView(self.bot, self.keyword, self.caller_id, "response"),
            embeds=[]
        )

        # Wait for user's next message
        def check(msg):
            return msg.author.id == interaction.user.id and msg.channel.id == interaction.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            new_response = msg.content.strip()

            # Delete the user's chat message to keep channel clean
            try:
                await msg.delete()
            except Exception:
                pass

            # Check for cancellation
            if new_response.lower() == "إلغاء":
                await prompt_message.edit(
                    content=f"{interaction.user.mention} **تم إلغاء العملية**",
                    view=FeatureAutoResponseView(self.bot, self.caller_id),
                    embeds=[]
                )
                return

            if not new_response:
                await prompt_message.edit(
                    content=f"{interaction.user.mention} ❌ يجب إدخال رد صالح.",
                    view=AutoRespEditOptionsView(self.bot, self.keyword, self.caller_id),
                    embeds=[]
                )
                return

            # Update the response in database
            bd = self.bot._bot_dir
            ar_data = _get_auto_responses(bd)
            ar_data[self.keyword] = new_response
            set_cfg("auto_responses", ar_data, bd)

            # Return to main menu with success message
            await prompt_message.edit(
                content=f"{interaction.user.mention} **إعداد الردود التلقائية**\nاختر إجراء للردود التلقائية:",
                view=FeatureAutoResponseView(self.bot, self.caller_id),
                embeds=[]
            )
            await interaction.followup.send(
                embed=_embed("✅ تم تعديل الرد التلقائي بنجاح!",
                             f"🔑 الكلمة: `{self.keyword}`\n"
                             f"💬 الرد الجديد: `{new_response[:80]}`", C.SUCCESS),
                ephemeral=True)

        except asyncio.TimeoutError:
            await prompt_message.edit(
                content=f"{interaction.user.mention} انتهى الوقت. حاول مرة أخرى.",
                view=FeatureAutoResponseView(self.bot, self.caller_id),
                embeds=[]
            )

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        """Return to keyword selection"""
        await interaction.response.defer(ephemeral=True)
        # Rebuild the keyword selection options
        ar_data = _get_auto_responses(self.bot._bot_dir)
        options = [
            discord.SelectOption(label=kw[:50], value=kw, description=rp[:80])
            for kw, rp in list(ar_data.items())[:25]
        ]
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **تعديل رد تلقائي**\nاختر الكلمة المفتاحية للتعديل:",
            embeds=[],
            view=AutoRespEditPickView(self.bot, options, self.caller_id))


class AutoRespEditCancelView(View):
    """View with cancel button for edit workflows"""
    def __init__(self, bot_ref, keyword: str, caller_id: int, edit_type: str):
        super().__init__(timeout=60)
        self.bot = bot_ref
        self.keyword = keyword
        self.caller_id = int(caller_id) if caller_id else None
        self.edit_type = edit_type  # "keyword" or "response"

        cancel_btn = discord.ui.Button(label="❌ إلغاء", style=discord.ButtonStyle.danger,
                                       custom_id="auto_resp_edit_cancel", row=0)
        cancel_btn.callback = self.cancel_btn
        self.add_item(cancel_btn)

    async def cancel_btn(self, interaction: discord.Interaction, button: Button = None):
        """Cancel the edit operation and return to main menu"""
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **تم إلغاء العملية**",
            view=FeatureAutoResponseView(self.bot, self.caller_id),
            embeds=[]
        )


# ── مساعد options الرتب ───────────────────────────────────────────────────────
def _guild_role_options(guild: discord.Guild) -> list:
    return [
        discord.SelectOption(label=r.name[:50], value=str(r.id))
        for r in sorted(guild.roles, key=lambda x: x.position, reverse=True)
        if not r.is_default() and not r.managed
    ][:25]


class RolePickView(View):
    """
    Generic: اختر رتبة وارجع للواجهة الصحيحة.
    back_embed_fn و back_view_cls يُحدَّدان من المُستدعي.
    """
    def __init__(self, bot_ref, cfg_key: str, title: str, options: list,
                 back_embed_fn=None, back_view_cls=None):
        super().__init__(timeout=None)
        self.bot          = bot_ref
        self.cfg_key      = cfg_key
        self.title        = title
        self.back_embed_fn = back_embed_fn
        self.back_view_cls = back_view_cls
        sel = discord.ui.Select(
            placeholder="اختر الرتبة...", options=options,
            custom_id=f"rpv_{cfg_key}_v6", row=0)
        sel.callback = self._on_select
        self.add_item(sel)

    async def _on_select(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔", ephemeral=True)
        role_id = int(interaction.data["values"][0])
        set_cfg(self.cfg_key, role_id, self.bot._bot_dir)
        reload_config_for(self.bot)
        
        role = interaction.guild.get_role(role_id)
        if self.back_embed_fn and self.back_view_cls:
            await interaction.edit_original_response(
                embed=self.back_embed_fn(self.bot, interaction.guild),
                view=self.back_view_cls(self.bot))
        else:
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
                embeds=[],
                view=Step3SettingsView(self.bot, self.caller_id))
        await interaction.followup.send(
            embed=_embed("✅ تم التحديد",
                         f"**{self.title}:** {role.mention if role else role_id}", C.SUCCESS),
            ephemeral=True)
        
        # If this is mute_role, sync permissions in background to avoid interaction timeout
        if self.cfg_key == "mute_role" and role:
            asyncio.create_task(_sync_mute_role_permissions(interaction.guild, role))

    @discord.ui.button(label="🔙  رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="rpv_back_v6", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        if self.back_embed_fn and self.back_view_cls:
            await interaction.edit_original_response(
                embed=self.back_embed_fn(self.bot, interaction.guild),
                view=self.back_view_cls(self.bot))
        else:
            await _back_to_step3(self.bot, interaction)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION E — مركز التحكم بالنظام + زر [ 🏗️ تثبيت وإنشاء النظام الفعلي ]
# ══════════════════════════════════════════════════════════════════════════════
def _dashboard_embed(bot_ref, guild: discord.Guild) -> discord.Embed:
    bd  = bot_ref._bot_dir
    def _ch(cid):
        if not cid: return "⬜"
        ch = guild.get_channel(int(cid))
        return ch.mention if ch else f"`{cid}`"
    def _role(rid):
        if not rid: return "⬜"
        r = guild.get_role(int(rid))
        return r.mention if r else f"`{rid}`"

    feat_lines = []
    for fkey, (emoji_key, name, _) in FEATURES.items():
        enabled = bool(cfg(fkey, bd))
        # Use unicode fallbacks for embed text to avoid raw emoji syntax
        feature_emoji_unicode = "📋"
        status_emoji_unicode = "✅" if enabled else "❌"
        feat_lines.append(f"{feature_emoji_unicode} {name}: {status_emoji_unicode}")

    return _embed(
        "🏰  مركز التحكم بالنظام",
        f"**🎬 روم الترحيب:** {_ch(cfg('welcome_channel', bd))}\n"
        f"**📋 روم اللوق:** {_ch(cfg('log_channel', bd))}\n"
        f"**⚖️ روم لوق العقوبات:** {_ch(cfg('sanctions_log_channel', bd))}\n"
        f"**🎭 روم الرتب التفاعلية:** {_ch(cfg('self_roles_channel', bd))}\n"
        f"{_sep()}"
        + "\n".join(feat_lines)
        + f"{_sep()}"
        "🏗️ **تثبيت وإنشاء النظام الفعلي** — ينشئ الكاتيجوري والغرف والصلاحيات برمجياً.\n"
        "✏️ **تعديل الإعدادات** — العودة للإعداد المتسلسل.\n"
        "🧹 **فرمتة** — مسح جميع الإعدادات.",
        C.GOLD,
        footer=f"System Bot  •  مركز التحكم  •  {_now_str()}"
    )


class DashboardView(View):
    def __init__(self, bot_ref, built: bool = False):
        super().__init__(timeout=None)
        self.bot   = bot_ref
        self.built = built

    @discord.ui.button(label="🔙  رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="dash_back_v8", row=0)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
            embeds=[],
            view=Step3SettingsView(self.bot, self.caller_id))

    @discord.ui.button(label="🏗️  إنشاء الإعدادات", style=discord.ButtonStyle.success,
                       custom_id="dash_build_v8", row=0)
    async def build_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        building_view = View(timeout=None)
        building_btn  = Button(label="⏳ جارٍ البناء...", style=discord.ButtonStyle.secondary, disabled=True)
        building_view.add_item(building_btn)
        await interaction.edit_original_response(
            embed=_embed("🏗️ جارٍ تثبيت النظام...",
                         "يرجى الانتظار — البوت ينشئ الكاتيجوري والغرف الآن.\n"
                         "هذا قد يستغرق بضع ثوانٍ.", C.WARNING),
            view=building_view)
        await _execute_build(self.bot, interaction)


class DashboardBuiltView(View):
    """الواجهة بعد اكتمال البناء — زرين فقط"""
    def __init__(self, bot_ref, caller_id: int = None):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.caller_id = int(caller_id) if caller_id else None

    @discord.ui.button(label="🧹  فورمات شامل", style=discord.ButtonStyle.danger,
                       custom_id="dash_reset_v8", row=0)
    async def reset_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        await interaction.followup.send_modal(HardResetModal(self.bot))

    @discord.ui.button(label="⚙️  تعديل الإعدادات", style=discord.ButtonStyle.primary,
                       custom_id="dash_edit_v8", row=0)
    async def edit_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("⛔ تحتاج صلاحية المدير.", ephemeral=True)
        await interaction.edit_original_response(
            embed=_step1_roles_embed(self.bot, interaction.guild),
            view=Step1RolesView(self.bot, interaction.user.id))


async def _execute_build(bot_ref, interaction: discord.Interaction):
    """
    🏗️ تنفيذ وتثبيت النظام:
    ينشئ كاتيجوري + غرف اللوق + الترحيب + الإجازات + يضبط الصلاحيات.
    """
    guild   = interaction.guild
    bd      = bot_ref._bot_dir
    results = []
    errors  = []
    bot_me  = guild.me
    owner   = guild.owner

    def _base_ow():
        ow = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            bot_me: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                                embed_links=True, attach_files=True),
        }
        if owner:
            ow[owner] = discord.PermissionOverwrite(view_channel=True, read_message_history=True)
        return ow

    async def _get_or_create_category(name: str) -> discord.CategoryChannel:
        cat = discord.utils.find(lambda c: c.name == name, guild.categories)
        if cat:
            return cat
        return await guild.create_category(name, overwrites=_base_ow())

    # 1️⃣ كاتيجوري نظام البوت
    try:
        sys_cat = await _get_or_create_category("🤖 نظام البوت")
        results.append(f"✅ كاتيجوري: {sys_cat.name}")
    except discord.Forbidden:
        errors.append("❌ لا صلاحية لإنشاء كاتيجوري")
        sys_cat = None
    except Exception as ex:
        errors.append(f"❌ كاتيجوري: {ex}")
        sys_cat = None

    # 2️⃣ روم اللوق المتقدم
    log_ch_id = cfg("log_channel", bd)
    if not (log_ch_id and guild.get_channel(int(log_ch_id))):
        try:
            ow = _base_ow()
            # فقط رتب admin ترى اللوق
            for rid in get_role_list("admin", bd):
                r = guild.get_role(rid)
                if r: ow[r] = discord.PermissionOverwrite(view_channel=True, read_message_history=True)
            for rid in get_role_list("owner", bd):
                r = guild.get_role(rid)
                if r: ow[r] = discord.PermissionOverwrite(view_channel=True, read_message_history=True)
            lch = await guild.create_text_channel(
                "📋・سجل-النشاط", category=sys_cat, overwrites=ow,
                topic="سجل نشاط السيرفر — حذف/تعديل الرسائل + دخول/خروج الأعضاء")
            set_cfg("log_channel", lch.id, bd)
            results.append(f"✅ روم اللوق: {lch.mention}")
        except Exception as ex:
            errors.append(f"❌ روم اللوق: {ex}")

    # 3️⃣ روم لوق العقوبات
    sl_ch_id = cfg("sanctions_log_channel", bd)
    if not (sl_ch_id and guild.get_channel(int(sl_ch_id))):
        try:
            ow = _base_ow()
            for rid in get_role_list("admin", bd) + get_role_list("owner", bd):
                r = guild.get_role(rid)
                if r: ow[r] = discord.PermissionOverwrite(view_channel=True, read_message_history=True)
            slch = await guild.create_text_channel(
                "⚖️・سجل-العقوبات", category=sys_cat, overwrites=ow,
                topic="سجل العقوبات الإدارية")
            set_cfg("sanctions_log_channel", slch.id, bd)
            results.append(f"✅ روم لوق العقوبات: {slch.mention}")
        except Exception as ex:
            errors.append(f"❌ روم لوق العقوبات: {ex}")

    # 4️⃣ روم الترحيب (عام — كل الأعضاء يرونه)
    wlc_ch_id = cfg("welcome_channel", bd)
    if not (wlc_ch_id and guild.get_channel(int(wlc_ch_id))):
        try:
            ow = {
                guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
                bot_me: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            }
            wch = await guild.create_text_channel(
                "🎬・الترحيب", category=sys_cat, overwrites=ow,
                topic="مرحباً بالأعضاء الجدد!")
            set_cfg("welcome_channel", wch.id, bd)
            results.append(f"✅ روم الترحيب: {wch.mention}")
        except Exception as ex:
            errors.append(f"❌ روم الترحيب: {ex}")

    reload_config_for(bot_ref)
    set_cfg("build_done", True, bd)

    # 5️⃣ روم الرتب التفاعلية (إن كانت مفعلة)
    if bool(cfg("feature_self_roles", bd)):
        src_ch_id = cfg("self_roles_channel", bd)
        if not (src_ch_id and guild.get_channel(int(src_ch_id))):
            try:
                src_ow = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
                    bot_me: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                                        embed_links=True),
                }
                src_ch = await guild.create_text_channel(
                    "🎭・الرتب-التفاعلية", category=sys_cat, overwrites=src_ow,
                    topic="اختر رتبك التفاعلية من هنا بضغطة زر!")
                set_cfg("self_roles_channel", src_ch.id, bd)
                # إرسال لوحة الرتب إن وجدت
                sr_cfg = _get_self_roles_config(bd)
                if sr_cfg:
                    await src_ch.send(view=SelfRolesPanel(bot_ref, sr_cfg))
                results.append(f"✅ روم الرتب التفاعلية: {src_ch.mention}")
            except Exception as ex:
                errors.append(f"❌ روم الرتب التفاعلية: {ex}")

    reload_config_for(bot_ref)
    set_cfg("build_done", True, bd)

    # ── رسالة النتيجة النهائية ────────────────────────────────────────────────
    summary = "\n".join(results) if results else "لا يوجد شيء جديد — كل الغرف كانت موجودة."
    if errors:
        summary += "\n\n" + "\n".join(errors)

    done_embed = _embed(
        "✅  تم بناء وتثبيت النظام بنجاح",
        f"{summary}\n\n"
        "جميع الإعدادات تم تطبيقها على السيرفر.\n"
        "الصلاحيات مُضبوطة — رتب الأونر والإداريين هم من يرون اللوق.",
        C.SUCCESS,
        footer=f"System Bot  •  مركز التحكم  •  {_now_str()}"
    )
    try:
        await interaction.edit_original_response(
            embed=done_embed,
            view=DashboardBuiltView(bot_ref))
    except Exception:
        pass


class HardResetModal(Modal, title="تأكيد الفرمتة الشاملة"):
    confirm = TextInput(label="اكتب RESET للتأكيد",
                        placeholder="RESET", required=True, max_length=10)
    def __init__(self, bot_ref):
        super().__init__()
        self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        if self.confirm.value.strip().upper() != "RESET":
            return await interaction.followup.send(
                embed=_embed("❌ تأكيد خاطئ", "اكتب `RESET` بالضبط.", C.DANGER), ephemeral=True)
        f = _cfg_file(self.bot._bot_dir)
        if os.path.isfile(f):
            os.remove(f)
        reload_config_for(self.bot)
        await interaction.edit_original_response(
            content="**🤖 System Bot Premium**\nمرحباً بك في لوحة التحكم\n\nاضغط **بدء 🚀** لبدء إعداد البوت خطوة بخطوة.",
            view=HubView(self.bot))
        await interaction.followup.send(
            embed=_embed("🧹 تم إعادة الضبط", "جميع الإعدادات تم مسحها.", C.WARNING),
            ephemeral=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION F — الأوامر الإدارية المخصصة (أسماء حرة + رتب حرة)
# ══════════════════════════════════════════════════════════════════════════════

# ── فئات الأوامر — 3 أقسام رئيسية + 2 متخصصة ───────────────────────────────
CMD_CATEGORIES = {
    "rooms":   {"label": "إعدادات الرومات الصوتية والكتابية",  "desc": "قفل/فتح/إخفاء + سحب أعضاء صوتياً"},
    "chat":    {"label": "إعدادات الشات",    "desc": "مسح الرسائل، بطء، تثبيت"},
    "admin":   {"label": "إعدادات الإدارة", "desc": "عقوبات، رتب، معلومات"},
    "intel":   {"label": "إعداد السيرفر",      "desc": "معلومات الأعضاء والسيرفر"},
}

# الأوامر المتاحة مع بياناتها الثابتة — 30 أمر في 5 فئات
ALL_ADMIN_ACTIONS = {
    # ── إعدادات الرومات الصوتية والكتابية ─────────────────────────────────────────
    "lock":          {"label": "قفل روم",                    "icon": "🔒", "cat": "rooms"},
    "unlock":        {"label": "فتح روم",                    "icon": "🔓", "cat": "rooms"},
    "hide":          {"label": "إخفاء روم",                  "icon": "🙈", "cat": "rooms"},
    "show":          {"label": "إظهار روم",                  "icon": "👁️", "cat": "rooms"},
    "move":          {"label": "سحب شخص صوتياً",            "icon": "🚀", "cat": "rooms"},
    "move_all":      {"label": "سحب الكل صوتياً",            "icon": "🌊", "cat": "rooms"},
    "disconnect":    {"label": "فصل صوتي",                  "icon": "🔌", "cat": "rooms"},
    "deafen":        {"label": "ديفن",                      "icon": "👂", "cat": "rooms"},
    "undeafen":      {"label": "فك الديفن",                  "icon": "🔔", "cat": "rooms"},
    # ── إعدادات الشات ────────────────────────────────────────────────────
    "clear":         {"label": "مسح الشات",                  "icon": "🧹", "cat": "chat"},
    "pin":           {"label": "تثبيت رسالة",                "icon": "📌", "cat": "chat"},
    "slowmode":      {"label": "وضع بطء",                    "icon": "🐢", "cat": "chat"},
    "mute_chat":     {"label": "كتم شات",                    "icon": "🔇", "cat": "chat"},
    "unmute_chat":   {"label": "فك كتم شات",                "icon": "💬", "cat": "chat"},
    # ── إعدادات الإدارة ──────────────────────────────────────────────────
    "kick":          {"label": "طرد",                        "icon": "👢", "cat": "admin"},
    "ban":           {"label": "باند",                        "icon": "🔨", "cat": "admin"},
    "tempban":       {"label": "باند مؤقت",                  "icon": "⏳", "cat": "admin"},
    "unban":         {"label": "فك باند",                    "icon": "🔓", "cat": "admin"},
    "timeout":       {"label": "سجن مؤقت",                  "icon": "⏱️", "cat": "admin"},
    "untimeout":     {"label": "فك سجن",                    "icon": "🕊️", "cat": "admin"},
    "warn":          {"label": "تحذير",                      "icon": "⚠️", "cat": "admin"},
    "mute":          {"label": "كتم صوت",                    "icon": "🔕", "cat": "admin"},
    "unmute":        {"label": "فك كتم صوت",                "icon": "🔊", "cat": "admin"},
    "strip_roles":   {"label": "سحب كل الرتب",              "icon": "✂️", "cat": "admin"},
    "nick":          {"label": "تغيير اسم",                  "icon": "✏️", "cat": "admin"},
    "give_role":     {"label": "إعطاء رتبة",                "icon": "🎁", "cat": "admin"},
    "take_role":     {"label": "سحب رتبة",                  "icon": "🗑️", "cat": "admin"},
    "jail":          {"label": "سجن",                        "icon": "🔒", "cat": "admin"},
    "unjail":        {"label": "إخراج من السجن",            "icon": "🔓", "cat": "admin"},
    # ── إعداد السيرفر ──────────────────────────────────────────────────────
    "userinfo":      {"label": "معلومات عضو",               "icon": "🔍", "cat": "intel"},
    "serverinfo":    {"label": "معلومات سيرفر",             "icon": "🏛️", "cat": "intel"},
    "roleinfo":      {"label": "معلومات رتبة",               "icon": "🎭", "cat": "intel"},
    "banlist":       {"label": "قائمة الباندات",             "icon": "📋", "cat": "intel"},
    "whois":         {"label": "من هو",                     "icon": "🕵️", "cat": "intel"},
}

# ── قراءة وكتابة إعدادات الأوامر ─────────────────────────────────────────────
def get_cmd_cfg(bot_dir=None) -> dict:
    """
    يُرجع dict: {action_key: {"name": str, "roles": [role_id, ...]}}
    """
    data = cfg("custom_cmd_cfg", bot_dir)
    if isinstance(data, dict):
        return data
    return {}

def set_cmd_cfg(data: dict, bot_dir=None):
    set_cfg("custom_cmd_cfg", data, bot_dir)

def _cmd_allowed(user: discord.Member, action: str, bot_dir=None) -> bool:
    """
    هل يملك المستخدم إذناً لتنفيذ هذا الأمر حسب الرتب المحددة في config فقط؟
    Uses the central admin permission check for silent denial.
    """
    return _has_admin_permission(user, bot_dir)

def _cmd_display_name(action: str, bot_dir=None) -> str:
    """يُرجع الاسم المخصص للأمر أو الاسم الافتراضي"""
    cmd_data = get_cmd_cfg(bot_dir)
    entry    = cmd_data.get(action, {})
    return entry.get("name") or ALL_ADMIN_ACTIONS[action]["label"]

def _cmd_target_protected(target: discord.Member, action: str, bot_dir=None) -> bool:
    """
    يتحقق إذا كان الهدف يملك رتبة محمية من هذا الأمر.
    إذا كان الهدف يملك أي رتبة من قائمة protected_roles لهذا الأمر → ممنوع.
    """
    cmd_data = get_cmd_cfg(bot_dir)
    entry    = cmd_data.get(action, {})
    protected_ids = [int(r) for r in entry.get("protected_roles", [])]
    if not protected_ids:
        return False
    target_role_ids = {r.id for r in target.roles}
    return bool(target_role_ids & set(protected_ids))

# ── واجهة إعداد الأوامر في الخطوة 3 ──────────────────────────────────────────
# Removed unwanted embed template as requested


class FeatureAdminCmdsView(View):
    """قائمة فئات الأوامر — المستوى الأول"""
    def __init__(self, bot_ref, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.is_shortcut = is_shortcut
        self.caller_id = None  # Will be set when called from Step3SettingsView

        # Build category options with emojis from emojis_config
        cat_options = []
        for cat_key, info in CMD_CATEGORIES.items():
            # Use CMD_CATEGORY_EMOJIS, leave emoji empty if not found
            emoji = emojis_config.CMD_CATEGORY_EMOJIS.get(cat_key)

            cat_options.append(
                discord.SelectOption(
                    label=info["label"], value=cat_key,
                    description=info["desc"],
                    emoji=emoji)
            )
        sel = discord.ui.Select(
            placeholder="اختر فئة الأوامر...",
            options=cat_options, custom_id="adm_cat_sel_v8", row=0)
        sel.callback = self._on_cat_select
        self.add_item(sel)

        # Back button - only add if not a shortcut
        if not self.is_shortcut:
            back_btn = discord.ui.Button(label="رجوع للقائمة", style=discord.ButtonStyle.secondary,
                                         custom_id="adm_cmd_back_v8", row=1)
            back_btn.callback = self.back_btn
            self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Silent ownership check - only allow caller to interact"""
        if self.caller_id and interaction.user.id != self.caller_id:
            return False  # Silently ignore without any response
        return True

    async def _on_cat_select(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("تحتاج صلاحية المدير.", ephemeral=True)
            return
        cat_key = interaction.data["values"][0]
        cmd_list_view = FeatureAdminCmdListView(self.bot, cat_key, self.is_shortcut)
        cmd_list_view.caller_id = self.caller_id
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **إعداد الأوامر — {CMD_CATEGORIES[cat_key]['label']}**\nاختر الأمر لإعداده:",
            view=cmd_list_view,
            embeds=[])

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        try:
            # Defer immediately to prevent timeout
            await interaction.response.defer()
            
            # If this is a shortcut, don't go back to step 3 - just close the view
            if self.is_shortcut:
                await interaction.edit_original_response(
                    content=f"{interaction.user.mention} **تم إغلاق لوحة التحكم**",
                    view=None,
                    embeds=[]
                )
                return
            
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **الخطوة 3: إعداد الميزات**\nاختر الميزة للضبط:",
                view=Step3SettingsView(self.bot, interaction.user.id),
                embeds=[])
        except discord.NotFound:
            # Handle 404 Unknown Webhook errors - interaction expired
            print(f"[SystemBot] Interaction expired in FeatureAdminCmdsView back button")
        except Exception as e:
            print(f"[SystemBot] Error in FeatureAdminCmdsView back button: {e}")


class FeatureAdminCmdListView(View):
    """قائمة الأوامر داخل فئة معينة"""
    def __init__(self, bot_ref, cat_key: str, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot = bot_ref
        self.cat_key = cat_key
        self.is_shortcut = is_shortcut
        self.caller_id = None  # Will be set when called from FeatureAdminCmdsView

        # Build command options with emojis from emojis_config
        options = [
            discord.SelectOption(
                label=info["label"][:50],
                value=action,
                description="اضغط لإعداد الاسم والرتب",
                emoji=emojis_config.ADMIN_COMMANDS_EMOJIS.get(action))
            for action, info in ALL_ADMIN_ACTIONS.items()
            if info.get("cat") == cat_key
        ]
        sel = discord.ui.Select(
            placeholder="اختر الأمر لإعداده...",
            options=options, custom_id=f"adm_cmd_sel_{cat_key}_v8", row=0)
        sel.callback = self._on_select
        self.add_item(sel)

        # Back button - always present in nested screens
        back_btn = discord.ui.Button(label="رجوع للفئات", style=discord.ButtonStyle.secondary,
                                     custom_id="adm_cmd_list_back_v8", row=1)
        back_btn.callback = self.back_btn
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Silent ownership check - only allow caller to interact"""
        if self.caller_id and interaction.user.id != self.caller_id:
            return False  # Silently ignore without any response
        return True

    async def _on_select(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("ليس لديك الصلاحية", ephemeral=True)
        action = interaction.data["values"][0]
        await interaction.response.send_modal(CmdNameModal(self.bot, action, self.cat_key, self.is_shortcut))

    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        try:
            # Defer immediately to prevent timeout
            await interaction.response.defer()
            admin_view = FeatureAdminCmdsView(self.bot, self.is_shortcut)
            admin_view.caller_id = self.caller_id
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} **إعداد الأوامر الإدارية**\nاختر فئة الأوامر:",
                view=admin_view,
                embeds=[])
        except discord.NotFound:
            # Handle 404 Unknown Webhook errors - interaction expired
            print(f"[SystemBot] Interaction expired in FeatureAdminCmdListView back button")
        except Exception as e:
            print(f"[SystemBot] Error in FeatureAdminCmdListView back button: {e}")


class CmdNameModal(Modal, title="إعداد الأمر — الاسم المخصص"):
    cmd_name = TextInput(
        label="الاسم المخصص للأمر (الأساسي)",
        placeholder="مثال: !ban أو !باند أو طرد",
        required=True, max_length=50)
    cmd_aliases = TextInput(
        label="أسماء بديلة (Aliases) — اختياري",
        placeholder="مثال: !باند, !حظر, !بان  (افصل بينها بفاصلة)",
        required=False, max_length=200)

    def __init__(self, bot_ref, action: str, cat_key: str = None, is_shortcut: bool = False):
        super().__init__()
        self.bot     = bot_ref
        self.action  = action
        self.cat_key = cat_key or ALL_ADMIN_ACTIONS[action].get("cat", "punish")
        self.is_shortcut = is_shortcut

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        name    = self.cmd_name.value.strip()
        action  = self.action
        # معالجة الأسماء البديلة — تنظيف وتقسيم
        raw_aliases = self.cmd_aliases.value or ""
        aliases = [a.strip() for a in raw_aliases.split(",") if a.strip() and a.strip() != name]
        aliases_display = ", ".join(f"`{a}`" for a in aliases) if aliases else "—"
        await interaction.edit_original_response(
            embed=_embed(
                f"إعداد: {ALL_ADMIN_ACTIONS[action]['label']}",
                f"الاسم الأساسي: **`{name}`**\n"
                f"الأسماء البديلة: {aliases_display}\n\n"
                "الآن اختر الرتب المسموح لها باستخدام هذا الأمر.\n"
                "يمكنك اختيار **أكثر من رتبة** من قائمة سيرفرك.",
                C.GOLD),
            view=CmdRoleSelectView(self.bot, action, name, self.cat_key, aliases, interaction.user.id, self.is_shortcut))


class CmdRoleSelectView(View):
    """اختيار الرتب المسموح لها بالأمر + الرتب المحمية"""
    def __init__(self, bot_ref, action: str, custom_name: str, cat_key: str = None, aliases: list = None, caller_id: int = None, is_shortcut: bool = False):
        super().__init__(timeout=None)
        self.bot         = bot_ref
        self.action      = action
        self.custom_name = custom_name
        self.cat_key     = cat_key or ALL_ADMIN_ACTIONS[action].get("cat", "punish")
        self.aliases     = aliases or []
        self.caller_id = int(caller_id) if caller_id else None
        self.is_shortcut = is_shortcut

        self._selected_roles: list[int]     = []
        self._protected_roles: list[int]    = []

        role_sel = discord.ui.RoleSelect(
            placeholder="اختر الرتب المسموح لها (متعدد)...",
            custom_id=f"cmd_role_sel_{action}_v8",
            min_values=1, max_values=25, row=0)
        role_sel.callback = self._on_roles
        self.add_item(role_sel)

        prot_sel = discord.ui.RoleSelect(
            placeholder="الرتب المحمية — لا يُنفَّذ الأمر عليها (اختياري)...",
            custom_id=f"cmd_prot_sel_{action}_v8",
            min_values=0, max_values=25, row=1)
        prot_sel.callback = self._on_protected
        self.add_item(prot_sel)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Silent ownership check - only allow caller to interact"""
        if self.caller_id and interaction.user.id != self.caller_id:
            return False  # Silently ignore without any response
        return True

    async def _on_roles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("ليس لديك الصلاحية", ephemeral=True)
        self._selected_roles = [int(v) for v in interaction.data["values"]]
        await interaction.edit_original_response(view=self)
        await interaction.followup.send(
            embed=_embed("رتب الإذن", f"تم تحديد **{len(self._selected_roles)}** رتبة مسموح لها.\nاضغط **حفظ** عند الانتهاء.", C.SUCCESS),
            ephemeral=True)

    async def _on_protected(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("ليس لديك الصلاحية", ephemeral=True)
        self._protected_roles = [int(v) for v in interaction.data["values"]]
        count = len(self._protected_roles)
        msg = f"تم تحديد **{count}** رتبة محمية." if count else "تم مسح الرتب المحمية."
        await interaction.edit_original_response(view=self)
        await interaction.followup.send(
            embed=_embed("الرتب المحمية", f"{msg}\nمن يملك هذه الرتب لا يُنفَّذ عليه الأمر.\nاضغط **حفظ** عند الانتهاء.", C.INFO),
            ephemeral=True)

    @discord.ui.button(label="حفظ", style=discord.ButtonStyle.success,
                       custom_id="cmd_role_save_v8", row=2)
    async def save_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("ليس لديك الصلاحية", ephemeral=True)
        if not self._selected_roles:
            return await interaction.followup.send(
                embed=_embed("تنبيه", "اختر رتبة واحدة على الأقل من قائمة الرتب المسموحة.", C.WARNING),
                ephemeral=True)
        bd       = self.bot._bot_dir
        cmd_data = get_cmd_cfg(bd)
        cmd_data[self.action] = {
            "name":            self.custom_name,
            "aliases":         self.aliases,
            "roles":           self._selected_roles,
            "protected_roles": self._protected_roles,
        }
        set_cmd_cfg(cmd_data, bd)
        roles_str   = " ".join(f"<@&{r}>" for r in self._selected_roles)
        prot_str    = " ".join(f"<@&{r}>" for r in self._protected_roles) if self._protected_roles else "—"
        aliases_str = ", ".join(f"`{a}`" for a in self.aliases) if self.aliases else "—"
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} **إعداد الأوامر — {CMD_CATEGORIES[self.cat_key]['label']}**\nاختر الأمر لإعداده:",
            view=FeatureAdminCmdListView(self.bot, self.cat_key, self.is_shortcut),
            embeds=[])
        await interaction.followup.send(
            embed=_embed("تم الحفظ",
                         f"الأمر **{ALL_ADMIN_ACTIONS[self.action]['label']}**\n"
                         f"الاسم الأساسي: `{self.custom_name}`\n"
                         f"الأسماء البديلة: {aliases_str}\n"
                         f"الرتب المسموحة: {roles_str}\n"
                         f"الرتب المحمية: {prot_str}", C.SUCCESS),
            ephemeral=True)

    @discord.ui.button(label="رجوع", style=discord.ButtonStyle.secondary,
                       custom_id="cmd_role_back_v8", row=2)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        cmd_list_view = FeatureAdminCmdListView(self.bot, self.cat_key, self.is_shortcut)
        cmd_list_view.caller_id = self.caller_id
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} **إعداد الأوامر — {CMD_CATEGORIES[self.cat_key]['label']}**\nاختر الأمر لإعداده:",
            view=cmd_list_view,
            embeds=[])


# ── واجهة تنفيذ الأوامر عبر /admin ───────────────────────────────────────────
class AdminActionView(View):
    """قائمة فئات الأوامر — المستوى الأول للتنفيذ"""
    def __init__(self, bot_ref):
        super().__init__(timeout=60)
        self.bot = bot_ref
        self.caller_id = None  # Will be set when called
        cat_options = [
            discord.SelectOption(
                label=info["label"], value=cat_key,
                description=info["desc"])
            for cat_key, info in CMD_CATEGORIES.items()
        ]
        sel = discord.ui.Select(
            placeholder="اختر فئة الأوامر...",
            options=cat_options, custom_id="admin_cat_sel_v8", row=0)
        sel.callback = self._on_cat_select
        self.add_item(sel)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Silent ownership check - only allow caller to interact"""
        if self.caller_id and interaction.user.id != self.caller_id:
            return False  # Silently ignore without any response
        return True

    async def _on_cat_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cat_key = interaction.data["values"][0]
        execute_view = AdminCmdExecuteView(self.bot, cat_key)
        execute_view.caller_id = self.caller_id
        await interaction.edit_original_response(
            embed=_embed(f"{CMD_CATEGORIES[cat_key]['label']}",
                         "اختر الأمر الذي تريد تنفيذه:", C.NAVY),
            view=execute_view)


class AdminCmdExecuteView(View):
    """قائمة الأوامر داخل فئة — للتنفيذ الفعلي"""
    def __init__(self, bot_ref, cat_key: str):
        super().__init__(timeout=60)
        self.bot = bot_ref
        self.cat_key = cat_key
        self.caller_id = None  # Will be set when called

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Silent ownership check - only allow caller to interact"""
        if self.caller_id and interaction.user.id != self.caller_id:
            return False  # Silently ignore without any response
        return True
        super().__init__(timeout=60)
        self.bot     = bot_ref
        self.cat_key = cat_key
        bd           = bot_ref._bot_dir
        cmd_data     = get_cmd_cfg(bd)
        options = []
        for action, info in ALL_ADMIN_ACTIONS.items():
            if info.get("cat") != cat_key:
                continue
            entry   = cmd_data.get(action, {})
            display = entry.get("name") or info["label"]
            options.append(discord.SelectOption(
                label=display[:50],
                value=action,
                description=info["label"],
                emoji=emojis_config.ADMIN_COMMANDS_EMOJIS.get(action, info.get("icon", "⚔️"))))
        if not options:
            options = [discord.SelectOption(label="لا أوامر مُعدَّة في هذه الفئة", value="_none")]
        sel = discord.ui.Select(
            placeholder="اختر الأمر للتنفيذ...",
            options=options[:25], custom_id=f"admin_exec_{cat_key}_v8", row=0)
        sel.callback = self._on_select
        self.add_item(sel)

    async def _on_select(self, interaction: discord.Interaction):
        action = interaction.data["values"][0]
        if action == "_none":
            return await interaction.response.send_message(
                embed=_embed("⚠️ لا أوامر", "لم يتم إعداد أوامر في هذه الفئة بعد.", C.WARNING), ephemeral=True)
        bd = self.bot._bot_dir
        if not _cmd_allowed(interaction.user, action, bd):
            return  # Silent denial - no response
        MODAL_MAP = {
            "kick":        KickModal,
            "ban":         BanModal,
            "tempban":     TempBanModal,
            "unban":       UnbanModal,
            "timeout":     TimeoutModal,
            "untimeout":   UnmuteModal,   # نفس منطق فك الكتم الصوتي — يرفع الـ timeout
            "warn":        WarnModal,
            "mute_chat":   MuteChatModal,
            "mute":        MuteModal,
            "strip_roles": StripRolesModal,
            "lock":        LockModal,
            "unlock":      UnlockModal,
            "hide":        HideModal,
            "show":        ShowModal,
            "clear":       ClearModal,
            "pin":         PinModal,
            "slowmode":    SlowmodeModal,
            "move":        MoveModal,
            "move_all":    MoveAllModal,
            "disconnect":  DisconnectModal,
            "nick":        NickModal,
            "give_role":   GiveRoleModal,
            "take_role":   TakeRoleModal,
            "unmute":      UnmuteModal,
            "unmute_chat": UnmuteChatModal,
            "userinfo":    UserInfoModal,
            "serverinfo":  ServerInfoModal,
            "roleinfo":    RoleInfoModal,
            "banlist":     BanListModal,
            "whois":       WhoisModal,
            "jail":        JailModal,
            "unjail":      UnjailModal,
        }
        ModalCls = MODAL_MAP.get(action)
        if ModalCls:
            await interaction.response.send_modal(ModalCls(self.bot))

    @discord.ui.button(label="🔙  رجوع للفئات", style=discord.ButtonStyle.secondary,
                       custom_id="admin_exec_back_v8", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            embed=_embed("⚔️ الأوامر الإدارية",
                         "اختر الفئة أولاً:", C.NAVY),
            view=AdminActionView(self.bot))


# ── Hierarchy فاحص الرتب ─────────────────────────────────────────────────────
def _top_role_pos(member: discord.Member) -> int:
    """أعلى موقع رتبة للعضو"""
    if not member.roles:
        return 0
    return max(r.position for r in member.roles)

def _get_rank(member: discord.Member, bot_dir=None) -> int:
    """
    يُرجع مستوى رتبة العضو حسب config فقط (لا يعتمد على صلاحيات ديسكورد):
    2 = Admins (manager_roles)
    1 = Member (member_roles)
    0 = لا شيء
    صاحب السيرفر → 2 دائماً
    """
    if member.id == member.guild.owner_id:
        return 2
    member_role_ids = {r.id for r in member.roles}
    for rank, cat_key in [(2, "manager"), (1, "member")]:
        cfg_role_ids = set(get_role_list(cat_key, bot_dir))
        if member_role_ids & cfg_role_ids:
            return rank
    return 0

def _has_bot_manager_permission(member: discord.Member, bot_dir=None) -> bool:
    """
    Dynamic Bot Manager permission check with fallback-enabled logic.
    Returns True if user has permission, False otherwise.
    
    Logic Rules:
    1. ALWAYS ALLOW: Server Owner (member.id == member.guild.owner_id)
    2. IF Bot Manager list IS EMPTY (len(bot_manager_roles) == 0):
       - Fallback to native Discord Administrator check (member.guild_permissions.administrator)
    3. IF Bot Manager list HAS ROLES (len(bot_manager_roles) > 0):
       - Native Discord Administrator permission is IGNORED/DISABLED
       - ONLY users holding at least one Bot Manager role are permitted
    
    This function is designed for SILENT denial - no error messages are sent.
    """
    # Check if user is Guild Owner (always has permission)
    if member.id == member.guild.owner_id:
        return True
    
    # Get configured Bot Manager roles (admin category with admin_roles cfg_key)
    bot_manager_roles = get_role_list("admin", bot_dir)
    
    # If Bot Manager list is empty, fallback to Discord Administrator permission
    if len(bot_manager_roles) == 0:
        return member.guild_permissions.administrator
    
    # If Bot Manager list has roles, Discord Administrator is ignored
    # Only users with at least one Bot Manager role are permitted
    member_role_ids = {r.id for r in member.roles}
    return bool(member_role_ids & set(bot_manager_roles))

def _has_admin_permission(member: discord.Member, bot_dir=None) -> bool:
    """
    Central permission check for administrative commands.
    Returns True if user has admin permission, False otherwise.
    Checks in order:
    1. Guild Owner (always has permission)
    2. Discord Administrator permission
    3. Discord Manage Roles permission
    4. Configured admin roles (admin_roles in system_config.json)
    
    If no roles are configured, only members with native Discord Administrator/Manage Roles permissions or Guild Owners can execute commands.
    This function is designed for SILENT denial - no error messages are sent.
    """
    # Check if user is Guild Owner
    if member.id == member.guild.owner_id:
        return True
    
    # Check if user has Discord Administrator permission
    if member.guild_permissions.administrator:
        return True
    
    # Check if user has Discord Manage Roles permission
    if member.guild_permissions.manage_roles:
        return True
    
    # Check configured admin roles
    admin_roles = get_role_list("admin", bot_dir)  # Uses admin_roles from config
    if admin_roles:
        # If admin roles are configured, user must have at least one
        member_role_ids = {r.id for r in member.roles}
        return bool(member_role_ids & set(admin_roles))
    
    # If no admin roles configured, only Discord Administrators, Manage Roles, and Guild Owners pass
    # (already checked above, so return False here)
    return False

def _can_act_on(actor: discord.Member, target: discord.Member,
                bot_dir=None) -> tuple[bool, str]:
    """
    يتحقق أن المنفذ يستطيع تنفيذ الأمر على الهدف.
    يُعيد (True, "") إذا مسموح، أو (False, "رسالة الخطأ") إذا ممنوع.

    الأولويات (مُحدَّثة v8.1):
    1. الهدف هو صاحب السيرفر → ممنوع دائماً
    2. الهدف هو بوت → ممنوع دائماً
    3. المنفذ هو صاحب السيرفر → مسموح (مع فحص رتبة البوت)
    4. فحص رتبة البوت: البوت يجب أن رتبته أعلى من الهدف
    5. فحص الصلاحية الإدارية حسب config فقط (لا Discord administrator)
    6. فحص الرتبة المساوية: رتبة المنفذ يجب أن تكون أعلى من الهدف
    """
    guild = actor.guild

    # ── 1. حماية صاحب السيرفر ────────────────────────────────────────────────
    if target.id == guild.owner_id:
        return False, "❌ لا يمكنك تنفيذ هذا الأمر على صاحب السيرفر!"

    # ── 2. حماية البوتات ─────────────────────────────────────────────────────
    if target.bot:
        return False, "❌ لا يمكنك تنفيذ هذا الأمر على بوت!"

    # ── 3. فحص رتبة البوت (Bot Permission Check) ─────────────────────────────
    # البوت يجب أن تكون رتبته أعلى من الهدف حتى يستطيع تنفيذ الأمر تقنياً
    bot_me = guild.me
    if bot_me and _top_role_pos(bot_me) <= _top_role_pos(target):
        return False, "❌ لا يمكنني تنفيذ الأمر لأن رتبة الشخص المستهدف أعلى من رتبتي في السيرفر!"

    # ── 4. صاحب السيرفر يستطيع فعل أي شيء ──────────────────────────────────
    if actor.id == guild.owner_id:
        return True, ""

    # ── 5. فحص الصلاحية عبر الرتب المحددة في config فقط ────────────────────
    # حتى لو كان لديه Administrator من ديسكورد، البوت يلتزم بالرتب المحددة
    bd = bot_dir
    actor_rank = _get_rank(actor, bd)
    if actor_rank < 2:
        return False, "❌ لا تملك رتبة إدارية معتمدة في إعدادات البوت لتنفيذ هذا الأمر!"

    # ── 6. منع تنفيذ الأمر على رتبة مساوية أو أعلى (Same Rank Protection) ───
    if _top_role_pos(actor) <= _top_role_pos(target):
        return False, "❌ لا يمكنك تنفيذ هذا الأمر على شخص يملك رتبة مساوية لك أو أعلى منك!"

    return True, ""

# ── Modals الأوامر ────────────────────────────────────────────────────────────
class KickModal(Modal, title="👢 طرد عضو"):
    target = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    reason = TextInput(label="سبب الطرد", required=False, max_length=200)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "kick", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        try:
            await member.send(f"تم طردك من سيرفر {interaction.guild.name} | السبب: {self.reason.value or '—'}")
        except Exception: pass
        await member.kick(reason=self.reason.value or "طرد إداري")
        log_content = f"""-------------------------------
# لوق طرد
العضو: {member.mention}
المنفذ: {interaction.user.mention}
السبب: {self.reason.value or '—'}
-------------------------------"""
        await _smart_log(interaction.guild, bd, "admin", log_content)
        await interaction.response.send_message(
            embed=_embed("✅ تم الطرد", f"{member.mention} تم طرده.", C.SUCCESS), ephemeral=True)


class BanModal(Modal, title="🔨 باند عضو"):
    target   = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    reason   = TextInput(label="سبب الباند", style=discord.TextStyle.paragraph, max_length=300)
    del_days = TextInput(label="حذف رسائله (0-7 أيام)", placeholder="0", required=False, max_length=1)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "ban", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        try:
            await member.send(f"تم حظرك بشكل دائم من سيرفر {interaction.guild.name} | السبب: {self.reason.value}")
        except Exception: pass
        del_d = max(0, min(7, int(self.del_days.value or 0)))
        await member.ban(reason=self.reason.value, delete_message_days=del_d)
        log_content = f"""-------------------------------
# لوق باند
المسؤول: {interaction.user.mention}
المعاقب: {member.mention}
العقوبه: باند
السبب: {self.reason.value or '—'}
المدة: دائم
حذف الرسائل: {del_d} أيام
-------------------------------"""
        await _smart_log(interaction.guild, bd, "sanctions", log_content)
        await interaction.response.send_message(
            embed=_embed("✅ تم الحظر", f"{member.mention} تم حظره نهائياً.", C.SUCCESS), ephemeral=True)


class TimeoutModal(Modal, title="⏱️ سجن مؤقت"):
    target   = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    duration = TextInput(label="المدة (مثال: 30m, 2h, 1d)", placeholder="60m", max_length=20)
    reason   = TextInput(label="سبب السجن", style=discord.TextStyle.paragraph, max_length=300)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        guild = interaction.guild
        member = await _resolve_member(guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "timeout", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        dur_secs = _parse_duration_seconds(self.duration.value)
        if dur_secs <= 0:
            dur_secs = 3600
        dur_secs = min(dur_secs, MAX_TIMEOUT_SECONDS)
        dur_str = _format_duration(dur_secs)
        until = discord.utils.utcnow() + datetime.timedelta(seconds=dur_secs)
        
        # Backup user's current roles before timeout
        saved_roles = save_muted_user_roles(member, bd)
        
        # Remove all active roles (except @everyone and managed) and apply timeout
        removable_roles = [r for r in member.roles if not r.is_default() and not r.managed]
        if removable_roles:
            await member.remove_roles(*removable_roles, reason="سجن مؤقت - حفظ الرتب")
        await member.timeout(until, reason=self.reason.value)
        
        try:
            await member.send(f"تم سجنك في سيرفر {guild.name} لمدة {dur_str} | السبب: {self.reason.value}")
        except Exception: pass
        log_content = f"""-------------------------------
# لوق سجن
المسؤول: {interaction.user.mention}
المعاقب: {member.mention}
العقوبه: تايم أوت
السبب: {self.reason.value or '—'}
المدة: {dur_str}
-------------------------------"""
        await _smart_log(guild, bd, "sanctions", log_content)
        
        # Schedule auto-restore after timeout
        async def _auto_restore():
            await asyncio.sleep(dur_secs)
            try:
                # FIRST: Restore saved roles BEFORE removing timeout
                saved_role_ids = load_muted_user_roles(member.id, bd)
                roles_to_restore = []
                for rid in saved_role_ids:
                    role_obj = guild.get_role(rid)
                    if role_obj and role_obj < guild.me.top_role:  # ensure bot has hierarchy permission
                        roles_to_restore.append(role_obj)
                
                if roles_to_restore:
                    print(f"[DEBUG] Restoring roles for {member.name}: {[r.name for r in roles_to_restore]}")
                    await member.add_roles(*roles_to_restore, reason="استعادة الرتب بعد انتهاء السجن")
                
                # SECOND: Remove timeout
                await member.timeout(None, reason="انتهت مدة السجن")
                
                # THIRD: Clear saved roles from backup
                clear_muted_user_roles(member.id, bd)
                
                log_restore = f"""-------------------------------
# لوق انتهاء تايم أوت
المعاقب: {member.mention}
المدة: {dur_str}
الحالة: تم استعادة الرتب المحفوظة
-------------------------------"""
                await _smart_log(guild, bd, "sanctions", log_restore)
            except Exception:
                pass
        asyncio.create_task(_auto_restore())
        
        await interaction.response.send_message(
            embed=_embed("✅ تم السجن", f"{member.mention} سُجن لمدة **{dur_str}**.", C.SUCCESS), ephemeral=True)


class WarnModal(Modal, title="⚠️ تحذير رسمي"):
    target = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    reason = TextInput(label="سبب التحذير", style=discord.TextStyle.paragraph, max_length=500)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "warn", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        dm_ok = False
        try:
            await member.send(f"تلقيت تحذيراً في سيرفر {interaction.guild.name} | المسؤول: {interaction.user.mention} | السبب: {self.reason.value}")
            dm_ok = True
        except Exception: pass
        log_content = f"""-------------------------------
# لوق تحذير
العضو: {member.mention}
المنفذ: {interaction.user.mention}
السبب: {self.reason.value}
حالة DM: {'مفتوح' if dm_ok else 'مغلق'}
-------------------------------"""
        await _smart_log(interaction.guild, bd, "admin", log_content)
        await interaction.response.send_message(
            embed=_embed("✅ تم التحذير",
                f"{member.mention} تم تحذيره.{' DM أُرسل.' if dm_ok else ' (DM مغلق)'}", C.SUCCESS),
            ephemeral=True)


class MuteModal(Modal, title="🔇 كتم صوتي"):
    target = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    reason = TextInput(label="سبب الكتم", required=False, max_length=200)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "mute", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        try: await member.edit(mute=True, reason=self.reason.value or "كتم إداري")
        except discord.Forbidden:
            return await interaction.response.send_message("❌ لا صلاحية للكتم — العضو ليس في روم صوتي.", ephemeral=True)
        log_content = f"""-------------------------------
# لوق كتم
المسؤول: {interaction.user.mention}
المعاقب: {member.mention}
العقوبه: كتم
السبب: {self.reason.value or '—'}
المدة: ---
-------------------------------"""
        await _smart_log(interaction.guild, bd, "sanctions", log_content)
        await interaction.response.send_message(
            embed=_embed("✅ تم الكتم", f"{member.mention} تم كتمه.", C.SUCCESS), ephemeral=True)


class UnmuteModal(Modal, title="🔊 فك الكتم"):
    target = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        guild = interaction.guild
        member = await _resolve_member(guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        
        # Remove mute role if configured
        mute_role_id = cfg("mute_role", bd)
        if mute_role_id:
            mute_role = guild.get_role(int(mute_role_id))
            if mute_role and mute_role in member.roles:
                await member.remove_roles(mute_role, reason="فك كتم")
        
        # Restore saved roles from backup
        saved_role_ids = load_muted_user_roles(member.id, bd)
        restored_roles = []
        for rid in saved_role_ids:
            r = guild.get_role(rid)
            if r:
                restored_roles.append(r)
        
        if restored_roles:
            await member.add_roles(*restored_roles, reason="استعادة الرتب بعد فك الكتم")
        
        # Clear saved roles from backup
        clear_muted_user_roles(member.id, bd)
        
        try: await member.edit(mute=False, reason="فك كتم")
        except discord.Forbidden:
            return await interaction.response.send_message("❌ لا صلاحية.", ephemeral=True)
        await interaction.response.send_message(
            embed=_embed("✅ تم فك الكتم", f"{member.mention} تم فك كتمه.", C.SUCCESS), ephemeral=True)


class UnbanModal(Modal, title="🔓 فك باند"):
    user_id = TextInput(label="ID المستخدم المحظور", placeholder="123456789012345678", max_length=20)
    reason  = TextInput(label="سبب رفع الحظر", required=False, max_length=200)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid  = int(self.user_id.value.strip())
            obj  = discord.Object(id=uid)
            await interaction.guild.unban(obj, reason=self.reason.value or "رفع حظر إداري")
            log_content = f"""-------------------------------
# لوق فك باند
المستخدم: {uid}
المنفذ: {interaction.user.mention}
السبب: {self.reason.value or '—'}
-------------------------------"""
            await _smart_log(interaction.guild, self.bot._bot_dir, "admin", log_content)
            await interaction.response.send_message(
                embed=_embed("✅ تم رفع الحظر", f"المستخدم `{uid}` تم رفع حظره.", C.SUCCESS), ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ ID غير صحيح.", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("❌ المستخدم غير محظور.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ لا صلاحية.", ephemeral=True)


class ClearModal(Modal, title="🧹 تطهير الرسائل"):
    amount = TextInput(label="عدد الرسائل (1-100)", placeholder="10", max_length=3)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        try: n = max(1, min(100, int(self.amount.value)))
        except ValueError: n = 10
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=n)
        log_content = f"""-------------------------------
# لوق تطهير رسائل
المنفذ: {interaction.user.mention}
الروم: {interaction.channel.mention}
الرسائل المحذوفة: {len(deleted)}
-------------------------------"""
        await _smart_log(interaction.guild, bd, "admin", log_content)
        await interaction.followup.send(
            embed=_embed("✅ تم التطهير", f"تم حذف **{len(deleted)}** رسالة.", C.SUCCESS), ephemeral=True)


class MoveModal(Modal, title="🚀 سحب عضو من روم"):
    target  = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    channel = TextInput(label="ID الروم الصوتي المقصود", placeholder="123456789012345678", max_length=20)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "move", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        try:
            ch_id = int(self.channel.value.strip())
            vc    = interaction.guild.get_channel(ch_id)
            if not vc or not isinstance(vc, discord.VoiceChannel):
                return await interaction.response.send_message("❌ الروم غير موجود أو ليس صوتياً.", ephemeral=True)
            import time as _time
            self.bot._pending_voice_actions[member.id] = {"executor": interaction.user, "action": "move", "ts": _time.time()}
            await member.move_to(vc, reason="سحب إداري")
            log_content = f"""-------------------------------
# لوق سحب
العضو: {member.mention}
المنفذ: {interaction.user.mention}
الروم: {vc.mention}
-------------------------------"""
            await _smart_log(interaction.guild, bd, "admin", log_content)
            await interaction.response.send_message(
                embed=_embed("✅ تم السحب", f"{member.mention} نُقل إلى {vc.mention}.", C.SUCCESS), ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ ID الروم غير صحيح.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ لا صلاحية للسحب.", ephemeral=True)


class GiveRoleModal(Modal, title="🎁 إعطاء رتبة"):
    target  = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    role_id = TextInput(label="ID الرتبة", placeholder="123456789012345678", max_length=20)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        
        # Strict permission check - must be first
        if not _has_bot_manager_permission(interaction.user, bd):
            return  # Silent denial - no response
        
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if _cmd_target_protected(member, "give_role", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        try:
            rid  = int(self.role_id.value.strip())
            role = interaction.guild.get_role(rid)
            if not role:
                return await interaction.response.send_message("❌ الرتبة غير موجودة.", ephemeral=True)
            await member.add_roles(role, reason=f"إعطاء رتبة بواسطة {interaction.user}")
            log_content = f"""-------------------------------
# لوق إعطاء رتبة
العضو: {member.mention}
المنفذ: {interaction.user.mention}
الرتبة: {role.mention}
-------------------------------"""
            await _smart_log(interaction.guild, bd, "admin", log_content)
            await interaction.response.send_message(
                embed=_embed("✅ تم الإعطاء", f"أُعطي {member.mention} رتبة {role.mention}.", C.SUCCESS), ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ ID الرتبة غير صحيح.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ لا صلاحية لإعطاء هذه الرتبة.", ephemeral=True)


class TakeRoleModal(Modal, title="✂️ سحب رتبة"):
    target  = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    role_id = TextInput(label="ID الرتبة", placeholder="123456789012345678", max_length=20)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        
        # Strict permission check - must be first
        if not _has_bot_manager_permission(interaction.user, bd):
            return  # Silent denial - no response
        
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "take_role", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        try:
            rid  = int(self.role_id.value.strip())
            role = interaction.guild.get_role(rid)
            if not role:
                return await interaction.response.send_message("❌ الرتبة غير موجودة.", ephemeral=True)
            # ── فحص: لا يمكن سحب رتبة أعلى من رتبة المنفذ ───────────────────
            actor_is_owner = (interaction.user.id == interaction.guild.owner_id)
            if not actor_is_owner and role.position >= _top_role_pos(interaction.user):
                return await interaction.response.send_message(
                    embed=_embed("🛡️ غير مسموح",
                                 "❌ لا يمكنك سحب رتبة أعلى من رتبتك أو مساوية لها!",
                                 C.DANGER), ephemeral=True)
            # ── فحص وجود الرتبة عند العضو (Role Existence Check) ──────────────
            if role not in member.roles:
                return await interaction.response.send_message(
                    embed=_embed("⚠️ الرتبة غير موجودة",
                                 "❌ هذا الشخص لا يملك هذه الرتبة أصلاً لإزالتها!",
                                 C.WARNING), ephemeral=True)
            await member.remove_roles(role, reason="سحب رتبة إداري")
            log_content = f"""-------------------------------
# لوق سحب رتبة
العضو: {member.mention}
المنفذ: {interaction.user.mention}
الرتبة: {role.mention}
-------------------------------"""
            await _smart_log(interaction.guild, bd, "admin", log_content)
            await interaction.response.send_message(
                embed=_embed("✅ تم السحب", f"سُحبت رتبة {role.mention} من {member.mention}.", C.SUCCESS), ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ ID الرتبة غير صحيح.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ لا صلاحية لسحب هذه الرتبة.", ephemeral=True)


class NickModal(Modal, title="✏️ تغيير اسم عضو"):
    target   = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    new_nick = TextInput(label="الاسم الجديد (فارغ = إعادة الأصلي)", required=False, max_length=32)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "nick", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        new_name = self.new_nick.value.strip() or None
        try: await member.edit(nick=new_name, reason="تغيير اسم إداري")
        except discord.Forbidden:
            return await interaction.response.send_message("❌ لا صلاحية لتغيير اسم هذا العضو.", ephemeral=True)
        log_content = f"""-------------------------------
# لوق تغيير اسم
العضو: {member.mention}
المنفذ: {interaction.user.mention}
الاسم الجديد: {new_name or 'الأصلي'}
-------------------------------"""
        await _smart_log(interaction.guild, bd, "admin", log_content)
        await interaction.response.send_message(
            embed=_embed("✅ تم التغيير",
                f"اسم {member.mention} → **{new_name or 'الأصلي'}**", C.SUCCESS), ephemeral=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION F2 — Modals الأوامر الجديدة (الـ 33 أمر كاملاً)
# ══════════════════════════════════════════════════════════════════════════════

class TempBanModal(Modal, title="⏳ باند مؤقت"):
    target   = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    duration = TextInput(label="المدة (مثال: 12h, 2d)", placeholder="24h", max_length=20)
    reason   = TextInput(label="السبب", style=discord.TextStyle.paragraph, max_length=300)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "tempban", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        dur_secs = _parse_duration_seconds(self.duration.value)
        if dur_secs <= 0:
            dur_secs = DEFAULT_TEMPBAN_SECONDS
        dur_str = _format_duration(dur_secs)
        try:
            await member.send(f"تم حظرك مؤقتاً من سيرفر {interaction.guild.name} لمدة {dur_str} | السبب: {self.reason.value}")
        except Exception: pass
        await member.ban(reason=f"باند مؤقت {dur_str} — {self.reason.value}", delete_message_days=0)
        # جدولة رفع الباند
        async def _auto_unban():
            await asyncio.sleep(dur_secs)
            try:
                await interaction.guild.unban(member, reason="انتهى الباند المؤقت")
            except Exception: pass
        asyncio.create_task(_auto_unban())
        log_content = f"""-------------------------------
# لوق باند مؤقت
المسؤول: {interaction.user.mention}
المعاقب: {member.mention}
العقوبه: باند مؤقت
السبب: {self.reason.value}
المدة: {dur_str}
-------------------------------"""
        await _smart_log(interaction.guild, bd, "sanctions", log_content)
        await interaction.response.send_message(
            embed=_embed("✅ باند مؤقت", f"{member.mention} مُحظور لمدة **{dur_str}**.", C.SUCCESS), ephemeral=True)


class MuteChatModal(Modal, title="🔇 كتم الشات"):
    target   = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    duration = TextInput(label="المدة (مثال: 30m, 2h, 1d)", placeholder="60m", max_length=20)
    reason   = TextInput(label="السبب", required=False, max_length=200)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "mute_chat", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        dur_secs = _parse_duration_seconds(self.duration.value)
        if dur_secs <= 0:
            dur_secs = 3600
        dur_secs = min(dur_secs, MAX_TIMEOUT_SECONDS)
        until = discord.utils.utcnow() + datetime.timedelta(seconds=dur_secs)
        await member.timeout(until, reason=self.reason.value or "كتم شات")
        dur_str = _format_duration(dur_secs)
        log_content = f"""-------------------------------
# لوق كتم شات
المسؤول: {interaction.user.mention}
المعاقب: {member.mention}
العقوبه: كتم شات
السبب: {self.reason.value or '—'}
المدة: {dur_str}
-------------------------------"""
        await _smart_log(interaction.guild, bd, "sanctions", log_content)
        await interaction.response.send_message(
            embed=_embed("✅ تم الكتم", f"{member.mention} مكتوم للشات {dur_str}.", C.SUCCESS), ephemeral=True)


class StripRolesModal(Modal, title="✂️ سحب كل الرتب"):
    target = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    reason = TextInput(label="السبب", required=False, max_length=200)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "strip_roles", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        removable = [r for r in member.roles if not r.is_default() and not r.managed
                     and r.position < interaction.guild.me.top_role.position]
        if removable:
            await member.remove_roles(*removable, reason=self.reason.value or "سحب كل الرتب")
        log_content = f"""-------------------------------
# لوق سحب كل الرتب
العضو: {member.mention}
المنفذ: {interaction.user.mention}
الرتب المحذوفة: {len(removable)}
السبب: {self.reason.value or '—'}
-------------------------------"""
        await _smart_log(interaction.guild, bd, "admin", log_content)
        await interaction.response.send_message(
            embed=_embed("✅ تم", f"تم سحب **{len(removable)}** رتبة من {member.mention}.", C.SUCCESS), ephemeral=True)


class LockModal(Modal, title="🔒 قفل روم"):
    channel = TextInput(label="ID الروم (اتركه فارغاً للروم الحالي)", required=False, max_length=20)
    reason  = TextInput(label="السبب", required=False, max_length=200)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if self.channel.value.strip():
            try: ch = guild.get_channel(int(self.channel.value.strip()))
            except: ch = interaction.channel
        else:
            ch = interaction.channel
        if not ch:
            return await interaction.response.send_message("❌ الروم غير موجود.", ephemeral=True)
        try:
            await ch.set_permissions(guild.default_role, send_messages=False,
                                     reason=self.reason.value or "قفل إداري")
            await interaction.response.send_message(
                embed=_embed("🔒 تم القفل", f"{ch.mention} مقفول.", C.WARNING), ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ لا صلاحية.", ephemeral=True)


class UnlockModal(Modal, title="🔓 فتح روم"):
    channel = TextInput(label="ID الروم (اتركه فارغاً للروم الحالي)", required=False, max_length=20)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if self.channel.value.strip():
            try: ch = guild.get_channel(int(self.channel.value.strip()))
            except: ch = interaction.channel
        else:
            ch = interaction.channel
        if not ch:
            return await interaction.response.send_message("❌ الروم غير موجود.", ephemeral=True)
        try:
            await ch.set_permissions(guild.default_role, send_messages=True)
            await interaction.response.send_message(
                embed=_embed("🔓 تم الفتح", f"{ch.mention} مفتوح.", C.SUCCESS), ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ لا صلاحية.", ephemeral=True)


class HideModal(Modal, title="🙈 إخفاء روم"):
    channel = TextInput(label="ID الروم (اتركه فارغاً للروم الحالي)", required=False, max_length=20)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        ch = (guild.get_channel(int(self.channel.value.strip()))
              if self.channel.value.strip() else interaction.channel)
        if not ch:
            return await interaction.response.send_message("❌ الروم غير موجود.", ephemeral=True)
        try:
            await ch.set_permissions(guild.default_role, view_channel=False)
            await interaction.response.send_message(
                embed=_embed("🙈 تم الإخفاء", f"الروم **{ch.name}** مخفي.", C.WARNING), ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ لا صلاحية.", ephemeral=True)


class ShowModal(Modal, title="👁️ إظهار روم"):
    channel = TextInput(label="ID الروم (اتركه فارغاً للروم الحالي)", required=False, max_length=20)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        ch = (guild.get_channel(int(self.channel.value.strip()))
              if self.channel.value.strip() else interaction.channel)
        if not ch:
            return await interaction.response.send_message("❌ الروم غير موجود.", ephemeral=True)
        try:
            await ch.set_permissions(guild.default_role, view_channel=True)
            await interaction.response.send_message(
                embed=_embed("👁️ تم الإظهار", f"الروم **{ch.name}** ظاهر الآن.", C.SUCCESS), ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ لا صلاحية.", ephemeral=True)


class PinModal(Modal, title="📌 تثبيت رسالة"):
    msg_id = TextInput(label="ID الرسالة", placeholder="123456789012345678", max_length=20)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        try:
            msg = await interaction.channel.fetch_message(int(self.msg_id.value.strip()))
            await msg.pin()
            await interaction.response.send_message(
                embed=_embed("📌 تم التثبيت", "الرسالة ثُبِّتت بنجاح.", C.SUCCESS), ephemeral=True)
        except Exception as ex:
            await interaction.response.send_message(f"❌ خطأ: {ex}", ephemeral=True)


class SlowmodeModal(Modal, title="🐢 وضع البطء"):
    channel = TextInput(label="ID الروم (فارغ = الحالي)", required=False, max_length=20)
    seconds = TextInput(label="التأخير بالثواني (0 = إيقاف)", placeholder="10", max_length=5)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        ch = (guild.get_channel(int(self.channel.value.strip()))
              if self.channel.value.strip() else interaction.channel)
        if not ch:
            return await interaction.response.send_message("❌ الروم غير موجود.", ephemeral=True)
        try:
            secs = max(0, min(21600, int(self.seconds.value)))
            await ch.edit(slowmode_delay=secs)
            msg = f"البطء: {secs} ثانية" if secs else "تم إيقاف البطء"
            await interaction.response.send_message(
                embed=_embed("🐢 Slowmode", f"{ch.mention} — {msg}", C.INFO), ephemeral=True)
        except Exception as ex:
            await interaction.response.send_message(f"❌ خطأ: {ex}", ephemeral=True)


class MoveAllModal(Modal, title="🌊 سحب الكل من الصوت"):
    from_ch = TextInput(label="ID الروم المصدر", placeholder="123456789012345678", max_length=20)
    to_ch   = TextInput(label="ID الروم الهدف", placeholder="123456789012345678", max_length=20)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd    = self.bot._bot_dir
        guild = interaction.guild
        try:
            src = guild.get_channel(int(self.from_ch.value.strip()))
            dst = guild.get_channel(int(self.to_ch.value.strip()))
            if not src or not isinstance(src, discord.VoiceChannel):
                return await interaction.response.send_message("❌ روم المصدر غير موجود أو ليس صوتياً.", ephemeral=True)
            if not dst or not isinstance(dst, discord.VoiceChannel):
                return await interaction.response.send_message("❌ روم الهدف غير موجود أو ليس صوتياً.", ephemeral=True)
            members_to_move = list(src.members)
            await interaction.response.defer(ephemeral=True)
            count = 0
            for m in members_to_move:
                try:
                    await m.move_to(dst, reason="سحب الكل — أمر إداري")
                    count += 1
                except Exception: pass
            log_content = f"""-------------------------------
# لوق سحب الكل
المنفذ: {interaction.user.mention}
من: {src.mention}
إلى: {dst.mention}
عدد المنقولين: {count}
-------------------------------"""
            await _smart_log(guild, bd, "admin", log_content)
            await interaction.followup.send(
                embed=_embed("✅ تم السحب", f"نُقل **{count}** عضو من {src.mention} إلى {dst.mention}.", C.SUCCESS), ephemeral=True)
        except ValueError:
            await interaction.followup.send("❌ ID غير صحيح.", ephemeral=True)


class DisconnectModal(Modal, title="🔌 فصل عضو صوتياً"):
    target = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    reason = TextInput(label="السبب", required=False, max_length=200)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "disconnect", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        try:
            import time as _time
            self.bot._pending_voice_actions[member.id] = {"executor": interaction.user, "action": "disconnect", "ts": _time.time()}
            await member.move_to(None, reason=self.reason.value or "فصل صوتي إداري")
            log_e = _embed("🔌 فصل صوتي",
                f"المنفذ: {interaction.user.mention}\nالهدف: {member.mention}", C.WARNING,
                footer=f"System Bot  •  Disconnect  •  {_now_str()}")
            await _smart_log(interaction.guild, bd, "admin", log_e)
            await interaction.response.send_message(
                embed=_embed("✅ تم الفصل", f"{member.mention} فُصل صوتياً.", C.SUCCESS), ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ لا صلاحية.", ephemeral=True)


class UnmuteChatModal(Modal, title="💬 فك كتم الشات"):
    target = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        try:
            await member.timeout(None, reason="فك كتم الشات")
            await interaction.response.send_message(
                embed=_embed("✅ تم فك الكتم", f"{member.mention} مفكوك كتمه.", C.SUCCESS), ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ لا صلاحية.", ephemeral=True)


class UserInfoModal(Modal, title="🔍 معلومات عضو"):
    target = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        roles = [r.mention for r in member.roles if not r.is_default()]
        e = _embed(f"🔍 {member.display_name}", "", C.INFO)
        e.add_field(name="الاسم الكامل", value=str(member), inline=True)
        e.add_field(name="ID", value=f"`{member.id}`", inline=True)
        e.add_field(name="انضم للسيرفر", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "—", inline=True)
        e.add_field(name="أنشأ الحساب", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        e.add_field(name="في روم صوتي", value=member.voice.channel.mention if member.voice else "لا", inline=True)
        e.add_field(name=f"الرتب ({len(roles)})", value=" ".join(roles[:10]) or "لا رتب", inline=False)
        e.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=e, ephemeral=True)


class ServerInfoModal(Modal, title="🏛️ معلومات السيرفر"):
    dummy = TextInput(label="اضغط إرسال للعرض", required=False, placeholder="—", max_length=1)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        g = interaction.guild
        e = _embed(f"🏛️ {g.name}", "", C.GOLD)
        e.add_field(name="ID", value=f"`{g.id}`", inline=True)
        e.add_field(name="الأعضاء", value=f"{g.member_count:,}", inline=True)
        e.add_field(name="البشر", value=f"{sum(1 for m in g.members if not m.bot):,}", inline=True)
        e.add_field(name="البوتات", value=f"{sum(1 for m in g.members if m.bot):,}", inline=True)
        e.add_field(name="الرتب", value=f"{len(g.roles)}", inline=True)
        e.add_field(name="الرومات", value=f"{len(g.channels)}", inline=True)
        e.add_field(name="تاريخ الإنشاء", value=g.created_at.strftime("%Y-%m-%d"), inline=True)
        e.add_field(name="الأونر", value=g.owner.mention if g.owner else "—", inline=True)
        if g.icon: e.set_thumbnail(url=g.icon.url)
        await interaction.response.send_message(embed=e, ephemeral=True)


class RoleInfoModal(Modal, title="🎭 معلومات رتبة"):
    role_id = TextInput(label="ID الرتبة", placeholder="123456789012345678", max_length=20)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        try:
            r = interaction.guild.get_role(int(self.role_id.value.strip()))
            if not r:
                return await interaction.response.send_message("❌ الرتبة غير موجودة.", ephemeral=True)
            count = sum(1 for m in interaction.guild.members if r in m.roles)
            e = _embed(f"🎭 {r.name}", "", C.from_rgb(*r.color.to_rgb()))
            e.add_field(name="ID", value=f"`{r.id}`", inline=True)
            e.add_field(name="الأعضاء", value=str(count), inline=True)
            e.add_field(name="الموقع", value=str(r.position), inline=True)
            e.add_field(name="اللون", value=str(r.color), inline=True)
            e.add_field(name="قابلة للمنشن", value="✅" if r.mentionable else "❌", inline=True)
            e.add_field(name="منفصلة في القائمة", value="✅" if r.hoist else "❌", inline=True)
            await interaction.response.send_message(embed=e, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ ID غير صحيح.", ephemeral=True)


class BanListModal(Modal, title="📋 قائمة المحظورين"):
    dummy = TextInput(label="اضغط إرسال للعرض", required=False, placeholder="—", max_length=1)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        bans = [entry async for entry in interaction.guild.bans(limit=20)]
        if not bans:
            return await interaction.followup.send(
                embed=_embed("📋 المحظورون", "لا يوجد محظورون.", C.INFO), ephemeral=True)
        lines = [f"`{b.user.id}` — **{b.user}**  |  {(b.reason or '—')[:40]}" for b in bans[:15]]
        await interaction.followup.send(
            embed=_embed(f"📋 المحظورون ({len(bans)}+)", "\n".join(lines), C.DANGER), ephemeral=True)


class WhoisModal(Modal, title="🕵️ من هو (Whois)"):
    target = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        member = await _resolve_member(interaction.guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        flags = []
        if member.bot: flags.append("🤖 بوت")
        if member.guild_permissions.administrator: flags.append("👑 مدير")
        if member.guild_permissions.manage_guild: flags.append("🛡️ مشرف")
        if member.premium_since: flags.append("💎 Nitro Booster")
        e = _embed(f"🕵️ {member.display_name}", " | ".join(flags) if flags else "عضو عادي", C.PURPLE)
        e.add_field(name="معرّف Discord", value=str(member), inline=True)
        e.add_field(name="ID", value=f"`{member.id}`", inline=True)
        e.add_field(name="في روم صوتي", value=member.voice.channel.name if member.voice else "لا", inline=True)
        e.add_field(name="الحالة", value=str(member.status), inline=True)
        e.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=e, ephemeral=True)


class JailModal(Modal, title="🔒 سجن عضو"):
    target   = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    duration = TextInput(label="المدة (مثال: 30m, 2h, 1d)", placeholder="دائم (اتركه فارغاً)", required=False, max_length=20)
    reason   = TextInput(label="سبب السجن", style=discord.TextStyle.paragraph, max_length=300)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        guild = interaction.guild
        member = await _resolve_member(guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        if _cmd_target_protected(member, "jail", bd):
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", "هذا الشخص يملك رتبة محمية — لا يمكن تنفيذ هذا الأمر عليه.", C.DANGER), ephemeral=True)
        
        jail_role_id = cfg("jail_role_id", bd)
        if not jail_role_id:
            return await interaction.response.send_message("❌ لم يتم تعيين رول السجن. يرجى ضبطه من إعدادات العقوبات.", ephemeral=True)
        jail_role = guild.get_role(int(jail_role_id))
        if not jail_role:
            return await interaction.response.send_message("❌ رول السجن غير موجود. يرجى ضبطه من إعدادات العقوبات.", ephemeral=True)
        if jail_role in member.roles:
            return await interaction.response.send_message("⚠️ العضو مسجون بالفعل.", ephemeral=True)
        
        # Parse duration
        dur_secs = _parse_duration_seconds(self.duration.value)
        dur_str = _format_duration(dur_secs) if dur_secs > 0 else "دائم"
        
        # Backup user's current roles before jailing
        saved_roles = save_jailed_user_roles(member, bd)
        
        # Remove all active roles and assign only jail role
        removable_roles = [r for r in member.roles if not r.is_default() and not r.managed]
        if removable_roles:
            await member.remove_roles(*removable_roles, reason=f"{interaction.client.JAIL_ACTION_NAME} - حفظ الرتب")
        await member.add_roles(jail_role, reason=f"{interaction.client.JAIL_ACTION_NAME} بأمر")
        
        if dur_secs > 0:
            # Schedule auto-unjail
            async def _auto_unjail():
                await asyncio.sleep(dur_secs)
                try:
                    # FIRST: Restore saved roles BEFORE removing jail role
                    saved_role_ids = load_jailed_user_roles(member.id, bd)
                    roles_to_restore = []
                    for rid in saved_role_ids:
                        role_obj = guild.get_role(rid)
                        if role_obj and role_obj < guild.me.top_role:  # ensure bot has hierarchy permission
                            roles_to_restore.append(role_obj)
                    
                    if roles_to_restore:
                        print(f"[DEBUG] Restoring roles for {member.name}: {[r.name for r in roles_to_restore]}")
                        await member.add_roles(*roles_to_restore, reason="استعادة الرتب بعد انتهاء السجن")
                    
                    # SECOND: Remove jail role
                    await member.remove_roles(jail_role, reason="انتهت مدة السجن")
                    
                    # THIRD: Clear saved roles from backup
                    clear_jailed_user_roles(member.id, bd)
                    
                    log_restore = f"""-------------------------------
# لوق انتهاء سجن
المعاقب: {member.mention}
المدة: {dur_str}
الحالة: تم استعادة الرتب المحفوظة
-------------------------------"""
                    await _smart_log(guild, bd, "sanctions", log_restore)
                except Exception:
                    pass
            asyncio.create_task(_auto_unjail())
        
        log_content = f"""-------------------------------
# لوق سجن
المسؤول: {interaction.user.mention}
المعاقب: {member.mention}
العقوبه: سجن
السبب: {self.reason.value or '—'}
المدة: {dur_str}
-------------------------------"""
        await _smart_log(guild, bd, "sanctions", log_content)
        await interaction.response.send_message(
            embed=_embed(f"✅ تم {interaction.client.JAIL_ACTION_NAME}", 
                f"{member.mention} مسجون لمدة **{dur_str}**.", C.SUCCESS), ephemeral=True)


class UnjailModal(Modal, title="🔓 إخراج من السجن"):
    target = TextInput(label="ID أو @mention العضو", placeholder="@عضو أو 123456789", max_length=30)
    def __init__(self, bot_ref):
        super().__init__(); self.bot = bot_ref
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot._bot_dir
        guild = interaction.guild
        member = await _resolve_member(guild, self.target.value)
        if not member:
            return await interaction.response.send_message("❌ العضو غير موجود.", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر على نفسك!", ephemeral=True)
        allowed, err_msg = _can_act_on(interaction.user, member, self.bot._bot_dir)
        if not allowed:
            return await interaction.response.send_message(
                embed=_embed("🛡️ محمي", err_msg, C.DANGER), ephemeral=True)
        
        jail_role_id = cfg("jail_role_id", bd)
        if jail_role_id:
            jail_role = guild.get_role(int(jail_role_id))
            if jail_role and jail_role in member.roles:
                await member.remove_roles(jail_role, reason=f"إخراج من {interaction.client.JAIL_CUSTOM_TITLE}")
        
        # Restore saved roles from backup
        saved_role_ids = load_jailed_user_roles(member.id, bd)
        restored_roles = []
        for rid in saved_role_ids:
            r = guild.get_role(rid)
            if r:
                restored_roles.append(r)
        
        if restored_roles:
            await member.add_roles(*restored_roles, reason=f"استعادة الرتب بعد الخروج من {interaction.client.JAIL_CUSTOM_TITLE}")
        
        # Clear saved roles from backup
        clear_jailed_user_roles(member.id, bd)
        
        log_e = _embed(f"🔓 إخراج من {interaction.client.JAIL_CUSTOM_TITLE}", 
            f"المنفذ: {interaction.user.mention}\nالهدف: {member.mention}", C.SUCCESS,
            footer=f"System Bot  •  {interaction.client.JAIL_CUSTOM_TITLE}  •  {_now_str()}")
        await _smart_log(guild, bd, "admin", log_e)
        await interaction.response.send_message(
            embed=_embed("✅ تم الإخراج", f"{member.mention} أُخرج من السجن.", C.SUCCESS), ephemeral=True)


# ══════════════════════════════════════════════════════════════════════════════
# MassDeleteChannelsView — حذف رومات جماعي بـ ChannelSelect
# ══════════════════════════════════════════════════════════════════════════════
class MassDeleteChannelsView(View):
    def __init__(self, bot_ref, executor: discord.Member):
        super().__init__(timeout=120)
        self.bot      = bot_ref
        self.executor = executor

        ch_sel = discord.ui.ChannelSelect(
            placeholder="📋  اختر الرومات للحذف (متعدد)...",
            custom_id="mass_del_ch_sel_v1",
            min_values=1, max_values=25, row=0)
        ch_sel.callback = self._on_select
        self.add_item(ch_sel)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.executor.id:
            return  # Silent denial - no response
        bd    = self.bot._bot_dir
        guild = interaction.guild
        if not _has_bot_manager_permission(interaction.user, bd):
            return  # Silent denial - no response

        selected_ids = [int(v) for v in interaction.data["values"]]
        await interaction.response.defer(ephemeral=True)

        success, failed = [], []
        for ch_id in selected_ids:
            ch = guild.get_channel(ch_id)
            if not ch:
                failed.append(f"`{ch_id}`")
                continue
            try:
                ch_name = ch.name
                await ch.delete(reason=f"حذف جماعي — {interaction.user.display_name}")
                success.append(f"**#{ch_name}**")
            except discord.Forbidden:
                failed.append(f"**#{ch.name}** (لا صلاحية)")
            except Exception:
                failed.append(f"**#{ch.name}**")

        # لوق
        if success:
            log_e = _embed(
                "🗑️ حذف رومات جماعي",
                f"المنفذ: {interaction.user.mention}\n"
                f"العدد: **{len(success)}** روم\n"
                f"الرومات: {' | '.join(success[:15])}",
                C.DANGER,
                footer=f"System Bot  •  MassDeleteChannels  •  {_now_str()}")
            await _smart_log(guild, bd, "admin", log_e)

        parts = []
        if success: parts.append(f"✅ تم حذف **{len(success)}**: {' | '.join(success[:10])}")
        if failed:  parts.append(f"❌ فشل **{len(failed)}**: {' | '.join(failed[:5])}")

        # تعطيل الـ view بعد التنفيذ
        for item in self.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception: pass

        await interaction.followup.send(
            embed=_embed("🗑️ نتيجة حذف الرومات",
                         "\n".join(parts) or "لم يتم حذف أي روم.", C.SUCCESS),
            ephemeral=True)




# ══════════════════════════════════════════════════════════════════════════════
# SECTION H — الكلاس الرئيسي SystemBot
# ══════════════════════════════════════════════════════════════════════════════
class SystemBot(discord.Client):
    def __init__(self, client_id: int, owner_discord_id: int,
                 bot_dir: str = None, allowed_guild_id: int = 0):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members         = True
        intents.guilds          = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

        self._client_id        = client_id
        self._owner_discord_id = owner_discord_id
        self._bot_dir          = bot_dir or _BASE
        self._allowed_guild    = allowed_guild_id

        # حقول الكونفيج — تُملأ في on_ready
        self.SETUP_CH         = 0
        self.WELCOME_CH       = 0
        self.LOG_CH           = 0
        self.SANCTIONS_LOG_CH = 0
        self.AUTO_ROLE        = 0
        self.LOG_VOICE_CH     = 0
        self.LOG_CHAT_CH      = 0
        self.LOG_ADMIN_CH     = 0
        self.LOG_JOIN_LEAVE_CH= 0
        self.JAIL_ROLE_ID     = 0
        self.JAIL_CUSTOM_TITLE= "سجن"
        self.JAIL_ACTION_NAME = "حبس"
        self.prohibited_words = []
        self.punishment_config = {}
        self._prohibited_word_patterns: list = []
        # ذاكرة مؤقتة: {member_id: {"executor": user, "action": "disconnect"|"move", "ts": float}}
        self._pending_voice_actions: dict = {}
        # ذاكرة للعقوبات المعلقة: {admin_message_id: {"target": member, "sanction_type": str, "revert_func": callable, "bot_dir": str}}
        self._pending_sanctions: dict = {}

    def _guild_ok(self, guild_id: int) -> bool:
        return not self._allowed_guild or guild_id == self._allowed_guild

    async def _sync_reaction_room_members_on_startup(self):
        """Sync reaction room members on startup - catch-up logic for state consistency with recovery"""
        bd = self._bot_dir
        
        # Check if reaction room feature is enabled
        if not bool(cfg("feature_reaction_room", bd)):
            return
        
        rr_ch_id = cfg("reaction_room_channel", bd)
        rr_msg_id = cfg("reaction_room_message_id", bd)
        rr_emoji = cfg("reaction_room_emoji", bd)
        rr_member_role_id = cfg("reaction_room_member_role", bd)
        rr_writer_role_id = cfg("reaction_room_writer_role", bd)
        
        if not all([rr_ch_id, rr_msg_id, rr_emoji, rr_member_role_id]):
            return
        
        # Load backup data for recovery
        backup_data = cfg("reaction_room_backup", bd) or {}
        
        for guild in self.guilds:
            if not self._guild_ok(guild.id):
                continue
            
            try:
                # Fetch the reaction room message
                ch = guild.get_channel(int(rr_ch_id))
                if not ch:
                    # Silently skip guilds where reaction room channel doesn't exist
                    continue
                
                msg = await ch.fetch_message(int(rr_msg_id))
                member_role = guild.get_role(int(rr_member_role_id))
                writer_role = guild.get_role(int(rr_writer_role_id)) if rr_writer_role_id else None
                
                if not member_role:
                    # Silently skip guilds where reaction room member role doesn't exist
                    continue
                
                # Get all users who reacted with the emoji
                reaction = None
                for r in msg.reactions:
                    try:
                        if str(r.emoji) == rr_emoji:
                            reaction = r
                            break
                    except Exception:
                        continue
                
                if not reaction:
                    # Silently skip guilds where reaction doesn't exist on message
                    continue
                
                # Get set of user IDs who have the reaction
                reactor_ids = set()
                async for user in reaction.users():
                    if not user.bot:
                        reactor_ids.add(user.id)
                
                # Get all members who have the member role
                role_members = set()
                for member in guild.members:
                    if member_role in member.roles and not member.bot:
                        role_members.add(member.id)
                
                # Find discrepancies
                should_have_role = reactor_ids - role_members  # Have reaction, no role
                should_not_have_role = role_members - reactor_ids  # Have role, no reaction
                
                print(f"[SystemBot] Reaction Room Sync for {guild.name}:")
                print(f"  - Users with reaction but no role: {len(should_have_role)}")
                print(f"  - Users with role but no reaction: {len(should_not_have_role)}")
                print(f"  - Backup data entries: {len(backup_data)}")
                
                # Grant role to users who have reaction but no role
                for user_id in should_have_role:
                    async def _grant_startup_role(uid=user_id):
                        try:
                            member = guild.get_member(uid)
                            if not member:
                                member = await guild.fetch_member(uid)
                            
                            if member and member_role:
                                await member.add_roles(member_role, reason="Reaction Room Startup Sync")
                                print(f"[SystemBot] ✅ Granted member role to {member.display_name}")
                        except discord.NotFound:
                            pass
                        except discord.Forbidden:
                            print(f"[SystemBot] ⚠️ Cannot grant role to user {uid} - permission denied")
                        except discord.HTTPException as e:
                            print(f"[SystemBot] ⚠️ HTTP error granting role to user {uid}: {e}")
                        except Exception as e:
                            print(f"[SystemBot] Error granting role to user {uid}: {e}")
                    asyncio.create_task(_grant_startup_role())
                
                # Remove role from users who have role but no reaction (unless whitelisted)
                for user_id in should_not_have_role:
                    async def _remove_startup_role(uid=user_id):
                        try:
                            member = guild.get_member(uid)
                            if not member:
                                member = await guild.fetch_member(uid)
                            
                            if member and member_role:
                                # Check if whitelisted (has writer role)
                                is_writer = writer_role and writer_role in member.roles
                                
                                if not is_writer:
                                    await member.remove_roles(member_role, reason="Reaction Room Startup Sync")
                                    print(f"[SystemBot] ✅ Removed member role from {member.display_name}")
                                else:
                                    print(f"[SystemBot] ⏭️ Skipped {member.display_name} (whitelisted - has writer role)")
                        except discord.NotFound:
                            pass
                        except discord.Forbidden:
                            print(f"[SystemBot] ⚠️ Cannot remove role from user {uid} - permission denied")
                        except discord.HTTPException as e:
                            print(f"[SystemBot] ⚠️ HTTP error removing role from user {uid}: {e}")
                        except Exception as e:
                            print(f"[SystemBot] Error removing role from user {uid}: {e}")
                    asyncio.create_task(_remove_startup_role())
                
                print(f"[SystemBot] ✅ Reaction Room sync completed for {guild.name}")
                
                # Restore roles from backup if any exist
                if backup_data:
                    print(f"[SystemBot] 🔄 Restoring roles from backup data")
                    for user_id_str, role_ids in backup_data.items():
                        async def _restore_backup_role(uid_str=user_id_str, r_ids=role_ids):
                            try:
                                user_id = int(uid_str)
                                member = guild.get_member(user_id)
                                if not member:
                                    member = await guild.fetch_member(user_id)
                                
                                if member:
                                    roles_to_restore = []
                                    for rid in r_ids:
                                        role_obj = guild.get_role(rid)
                                        if role_obj and role_obj < guild.me.top_role:
                                            roles_to_restore.append(role_obj)
                                    
                                    if roles_to_restore:
                                        await member.add_roles(*roles_to_restore, reason="Reaction Room Backup Recovery")
                                        print(f"[SystemBot] ✅ Restored roles for {member.display_name} from backup")
                            except Exception as e:
                                print(f"[SystemBot] ⚠️ Error restoring from backup for user {uid_str}: {e}")
                        asyncio.create_task(_restore_backup_role())
                    
                    # NOTE: Backup data is NOT cleared to maintain persistent reaction tracking state
                    # This ensures reaction events continue to work after bot restart
                
            except discord.NotFound:
                # Silently skip - reaction room message may not exist in all guilds
                pass
            except discord.Forbidden:
                # Silently skip - bot may not have permission in all guilds
                pass
            except discord.HTTPException as e:
                print(f"[SystemBot] ⚠️ HTTP error syncing reaction room in guild {guild.name}: {e}")
            except Exception as e:
                print(f"[SystemBot] Error syncing reaction room in guild {guild.name}: {e}")

    async def _ensure_system_role(self):
        """Ensure System {Guild_Name} role exists with Administrator permissions for each guild"""
        for guild in self.guilds:
            if not self._guild_ok(guild.id):
                continue
            
            try:
                # Look for existing System role
                system_role_name = f"System {guild.name}"
                system_role = None
                
                for role in guild.roles:
                    if role.name.startswith("System ") and role.permissions.administrator:
                        system_role = role
                        # Update name if guild name changed
                        if role.name != system_role_name:
                            try:
                                await role.edit(name=system_role_name, reason="Update System role name")
                                print(f"[SystemBot] Updated System role name to: {system_role_name}")
                            except Exception as e:
                                print(f"[SystemBot] Error updating System role name: {e}")
                        break
                
                # Create if not exists
                if not system_role:
                    try:
                        system_role = await guild.create_role(
                            name=system_role_name,
                            permissions=discord.Permissions(administrator=True),
                            reason="System role created by bot"
                        )
                        print(f"[SystemBot] Created System role: {system_role_name}")
                    except Exception as e:
                        print(f"[SystemBot] Error creating System role: {e}")
            except Exception as e:
                print(f"[SystemBot] Error ensuring System role for {guild.name}: {e}")

    # ── on_ready ─────────────────────────────────────────────────────────────
    async def on_ready(self):
        print(f"[SystemBot] ✅ {self.user} — متصل")
        reload_config_for(self)
        
        # Cleanup duplicate background images on startup
        v2_cleanup_duplicate_backgrounds()
        
        # Ensure System {Guild_Name} role exists for each guild
        await self._ensure_system_role()
        
        # Sync mute role permissions across all channels
        mute_id = cfg("mute_role", self._bot_dir)
        if mute_id:
            for guild in self.guilds:
                if self._guild_ok(guild.id):
                    mute_role = guild.get_role(int(mute_id))
                    if mute_role:
                        await _sync_mute_role_permissions(guild, mute_role)
        
        # Sync jail role permissions across all channels
        jail_id = cfg("jail_role_id", self._bot_dir)
        jail_ch_id = cfg("jail_channel_id", self._bot_dir)
        if jail_id:
            for guild in self.guilds:
                if self._guild_ok(guild.id):
                    jail_role = guild.get_role(int(jail_id))
                    if jail_role:
                        await _sync_jail_role_permissions(guild, jail_role, jail_ch_id)
        
        # Restore active punishments and timers from backup
        await self._restore_active_punishments()
        
        # Sync reaction room members on startup
        await self._sync_reaction_room_members_on_startup()
        
        # إعادة تسجيل Views الدائمة
        self.add_view(HubView(self))
        # SelfRolesPanel — يُسجَّل بالرتب الحالية من الكونفيج
        sr_cfg = _get_self_roles_config(self._bot_dir)
        if sr_cfg:
            self.add_view(SelfRolesPanel(self, sr_cfg))
        # Register FeatureReactionRoomView if reaction room feature is enabled
        if bool(cfg("feature_reaction_room", self._bot_dir)):
            self.add_view(FeatureReactionRoomView(self))
        # تسجيل الأوامر
        await self._register_commands()
        try:
            # Clear all guild-level commands for every joined guild to eliminate lingering local commands
            for guild in self.guilds:
                try:
                    self.tree.clear_commands(guild=guild)
                    print(f"[SystemBot] Cleared guild commands for {guild.name}")
                except Exception as ex:
                    print(f"[SystemBot] Error clearing guild commands for {guild.name}: {ex}")
            
            # Sync ONCE globally
            await self.tree.sync()
            print(f"[SystemBot] ✅ الأوامر مُزامنة (global)")
        except Exception as ex:
            print(f"[SystemBot] ⚠️ خطأ مزامنة الأوامر: {ex}")
        # إرسال لوحة الإعداد إن لم تُرسَل من قبل
        setup_ch_id = cfg("setup_channel", self._bot_dir)
        if setup_ch_id:
            for g in self.guilds:
                if not self._guild_ok(g.id):
                    continue
                ch = g.get_channel(int(setup_ch_id))
                if ch:
                    try:
                        # لا نرسل مجدداً — نكتفي بتسجيل الـ view
                        pass
                    except Exception:
                        pass
    
    async def _restore_active_punishments(self):
        """Restore active punishments from backup and restart timers on bot startup"""
        bd = self._bot_dir
        for guild in self.guilds:
            if not self._guild_ok(guild.id):
                continue
            
            # Restore mutes: Check members who have mute role and restore their roles
            mute_id = cfg("mute_role", bd)
            if mute_id:
                mute_role = guild.get_role(int(mute_id))
                if mute_role:
                    # Find all members with mute role
                    for member in guild.members:
                        if mute_role in member.roles:
                            # This member is muted, ensure their roles are backed up
                            saved_roles = load_muted_user_roles(member.id, bd)
                            if not saved_roles:
                                # Backup current roles if not already backed up
                                save_muted_user_roles(member, bd)
                            print(f"[SystemBot] 🔇 Restored mute for {member.display_name} in {guild.name}")
            
            # Restore jails: Check members who have jail role and restore their roles
            jail_id = cfg("jail_role_id", bd)
            if jail_id:
                jail_role = guild.get_role(int(jail_id))
                if jail_role:
                    # Find all members with jail role
                    for member in guild.members:
                        if jail_role in member.roles:
                            # This member is jailed, ensure their roles are backed up
                            saved_roles = load_jailed_user_roles(member.id, bd)
                            if not saved_roles:
                                # Backup current roles if not already backed up
                                save_jailed_user_roles(member, bd)
                            print(f"[SystemBot] 🔒 Restored jail for {member.display_name} in {guild.name}")
        
        print(f"[SystemBot] ✅ Active punishments restored across {len(self.guilds)} guilds")

    # ── on_guild_join ─────────────────────────────────────────────────────────
    async def on_guild_join(self, guild: discord.Guild):
        if not self._guild_ok(guild.id):
            return
        # Disabled automatic channel/category creation on join
        # The bot will not create default channels or categories when joining a server
        print(f"[SystemBot] انضم للسيرفر: {guild.name} (لا يتم إنشاء قنوات تلقائياً)")

    # ── on_member_join ────────────────────────────────────────────────────────
    async def on_member_join(self, member: discord.Member):
        if not self._guild_ok(member.guild.id):
            return
        guild = member.guild
        guild_id = guild.id
        bd    = self._bot_dir

        # Active Sanction Roles Verification - Prevent role conflicts
        mute_role_id = cfg("mute_role", bd)
        jail_role_id = cfg("jail_role_id", bd)
        
        # Check if member has active jail or mute role
        has_active_sanction = False
        if mute_role_id and any(r.id == int(mute_role_id) for r in member.roles):
            has_active_sanction = True
        if jail_role_id and any(r.id == int(jail_role_id) for r in member.roles):
            has_active_sanction = True

        # Auto Role — فحص التفعيل أولاً
        if bool(cfg("feature_auto_role", bd)) and not has_active_sanction:
            ar_id = cfg("auto_role", bd)
            if ar_id:
                ar = guild.get_role(int(ar_id))
                if ar:
                    try:
                        await member.add_roles(ar)
                    except Exception:
                        pass

        # Interactive Roles — send panel DM if feature enabled
        if bool(cfg("feature_self_roles", bd)):
            src_id = cfg("self_roles_channel", bd)
            if src_id:
                src_ch = guild.get_channel(int(src_id))
                if src_ch:
                    try:
                        await member.send(
                            embed=_embed(
                                "🎭  الرتب التفاعلية",
                                f"مرحباً {member.display_name}!\n"
                                f"يمكنك اختيار رتبك التفاعلية في {src_ch.mention} 🎉",
                                C.PURPLE
                            )
                        )
                    except Exception:
                        pass

        # لوق دخول العضو
        if bool(cfg("feature_log", bd)):
            date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            log_content = f"""-------------------------------
# لوق دخول
العضو: {member.mention}
المعرف: {member.id}
التاريخ: {date_str}
-------------------------------"""
            await _smart_log(guild, bd, "join_leave", log_content)

        # Welcome Image - V2 System
        if not bool(_guild_cfg("welcome_enabled", guild_id, bd)):
            return
        wch_id = _guild_cfg("welcome_channel", guild_id, bd)
        if not wch_id:
            return
        wch = guild.get_channel(int(wch_id))
        if not wch:
            return
        try:
            # Check if guild has background URL in server_images.json
            bg_url = _get_guild_image_url(guild_id)
            if not bg_url:
                print(f"[V2 Welcome] Error: No welcome_bg_url found in server_images.json for guild {guild_id}")
                import traceback
                traceback.print_exc()
                # Send text error message only - NO IMAGE GENERATION
                await wch.send(f"⚠️ يوجد خطأ: لم يتم رفع صورة خلفية لهذا السيرفر بعد، يرجى رفع صورة أولاً.\n{member.mention}")
                return
            
            # Fetch background from unified storage - NO FALLBACK
            bg_bytes = await v2_fetch_background_image(guild_id, bd, self)
            
            if not bg_bytes:
                print(f"[V2 Welcome] Error: Failed to fetch background bytes for guild {guild_id}")
                import traceback
                traceback.print_exc()
                # Send text error message only - NO IMAGE GENERATION
                await wch.send(f"⚠️ يوجد خطأ: تعذر تحميل صورة الخلفية. راجع الـ Terminal للتفاصيل.\n{member.mention}")
                return
            
            # Get avatar URL
            avatar_url = member.display_avatar.with_format("png").url
            
            # Get custom coordinates and size from config
            avatar_x = _guild_cfg("welcome_avatar_x", guild_id, bd)
            avatar_y = _guild_cfg("welcome_avatar_y", guild_id, bd)
            avatar_size = _guild_cfg("welcome_avatar_size", guild_id, bd) or 200
            
            # Generate welcome card with avatar only and custom coordinates
            img_bytes = await v2_generate_welcome_card(avatar_url, bg_bytes, avatar_size, avatar_x, avatar_y)
            
            if not img_bytes:
                print(f"[V2 Welcome] Error: Failed to generate welcome card for guild {guild_id}")
                import traceback
                traceback.print_exc()
                # Send text error message only - NO IMAGE GENERATION
                await wch.send(f"⚠️ يوجد خطأ: تعذر توليد بطاقة الترحيب. راجع الـ Terminal للتفاصيل.\n{member.mention}")
                return
            
            # Send the welcome image - FIRST MESSAGE (image only)
            file = discord.File(io.BytesIO(img_bytes), filename="welcome.png")
            await wch.send(file=file)

            # Send formatted chat message - SECOND MESSAGE (below the image)
            # Get formatting config
            formatting_config = _guild_cfg("welcome_formatting", guild_id, bd) or {}
            
            # Get the base message text
            message_text = formatting_config.get("chat_message_text", "مرحباً بك في السيرفر!")
            
            # Apply dynamic formatting
            formatted_message = message_text
            
            # Replace member mention with member.mention (e.g., <@USER_ID>)
            if formatting_config.get("enable_mention", False):
                mention_trigger = formatting_config.get("mention_trigger", "")
                if mention_trigger:
                    formatted_message = formatted_message.replace(mention_trigger, member.mention)
            
            # Replace owner mention - fetch owner safely and use explicit format
            if formatting_config.get("enable_owner", False):
                owner_trigger = formatting_config.get("owner_trigger", "")
                if owner_trigger:
                    try:
                        # Try to get owner from guild.owner first
                        owner = guild.owner
                        if not owner:
                            # Fallback to fetch by ID
                            owner = await guild.fetch_member(guild.owner_id)
                        if owner:
                            # Replace with explicit Discord mention format <@USER_ID>
                            formatted_message = formatted_message.replace(owner_trigger, f"<@{owner.id}>")
                    except Exception as ex:
                        print(f"[SystemBot] Error fetching owner for mention: {ex}")
            
            # Replace server mention with guild name
            if formatting_config.get("enable_server", False):
                server_trigger = formatting_config.get("server_trigger", "")
                if server_trigger:
                    formatted_message = formatted_message.replace(server_trigger, guild.name)
            
            # Replace member count
            if formatting_config.get("enable_count", False):
                count_trigger = formatting_config.get("count_trigger", "")
                if count_trigger:
                    formatted_message = formatted_message.replace(count_trigger, str(guild.member_count))
            
            # Replace channel shortcuts with proper regex cleaning and validation
            channel_shortcuts = formatting_config.get("channel_shortcuts", [])
            if channel_shortcuts:
                for shortcut in channel_shortcuts:
                    shortcut_trigger = shortcut.get("shortcut", "")
                    channel_id_input = shortcut.get("channel_id", "")
                    if shortcut_trigger and channel_id_input:
                        # Clean the input channel ID/Link using regex to extract raw channel ID numbers
                        extracted_id_match = re.search(r'\d+', channel_id_input)
                        if extracted_id_match:
                            extracted_id = extracted_id_match.group()
                            try:
                                # Convert extracted ID to integer
                                channel_id = int(extracted_id)
                                # Check if the channel exists in the guild
                                if guild.get_channel(channel_id):
                                    # Replace the shortcut with proper Discord channel mention
                                    formatted_message = formatted_message.replace(shortcut_trigger, f"<#{channel_id}>")
                            except ValueError:
                                print(f"[SystemBot] Invalid channel ID format: {extracted_id}")
                                pass
            
            # Apply bold formatting
            if formatting_config.get("enable_bold", False):
                bold_trigger = formatting_config.get("bold_trigger", "")
                if bold_trigger:
                    formatted_message = formatted_message.replace(bold_trigger, f"**{bold_trigger}**")
            
            # Apply italic formatting
            if formatting_config.get("enable_italic", False):
                italic_trigger = formatting_config.get("italic_trigger", "")
                if italic_trigger:
                    formatted_message = formatted_message.replace(italic_trigger, f"*{italic_trigger}*")
            
            # Send the formatted message
            await wch.send(content=formatted_message)
        except Exception as ex:
            print(f"[SystemBot] ⚠️ خطأ Welcome: {ex}")

    # ── on_voice_state_update — لوق الصوت ────────────────────────────────────
    async def on_voice_state_update(self, member: discord.Member,
                                    before: discord.VoiceState,
                                    after:  discord.VoiceState):
        if not self._guild_ok(member.guild.id):
            return
        if not bool(cfg("feature_log", self._bot_dir)):
            return
        guild = member.guild
        bd    = self._bot_dir

        # تحديد نوع الحدث
        if before.channel is None and after.channel is not None:
            title  = "دخول روم صوتي"
            color  = C.SUCCESS.value
            detail = after.channel.mention
        elif before.channel is not None and after.channel is None:
            import time as _time
            # أولاً: هل المنفذ محفوظ في الذاكرة (أوامر البوت)؟
            pending = self._pending_voice_actions.pop(member.id, None)
            if pending and (_time.time() - pending["ts"]) < 10:
                voice_kicked_by = pending["executor"]
            else:
                # ثانياً: تحقق من audit log (طرد من بروفايل أو يدوي)
                await asyncio.sleep(1)
                voice_kicked_by = None
                try:
                    now = datetime.datetime.now(datetime.timezone.utc)
                    async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_disconnect):
                        age = (now - entry.created_at).total_seconds()
                        if age > 10:
                            break
                        if not entry.user.bot:
                            voice_kicked_by = entry.user
                        break
                except Exception:
                    pass

            if voice_kicked_by and voice_kicked_by != member:
                title  = "تم طرده من الروم الصوتي"
                color  = C.DANGER.value
                detail = (f"طرده: {voice_kicked_by.mention}\n"
                          f"الروم: {before.channel.mention}")
            else:
                title  = "خروج من روم صوتي"
                color  = C.GRAPHITE.value
                detail = before.channel.mention
        elif before.channel != after.channel:
            import time as _time
            # أولاً: هل المنفذ محفوظ في الذاكرة (أوامر البوت)؟
            pending = self._pending_voice_actions.pop(member.id, None)
            if pending and (_time.time() - pending["ts"]) < 10:
                moved_by = pending["executor"]
            else:
                # ثانياً: تحقق من audit log
                await asyncio.sleep(1)
                moved_by = None
                try:
                    now = datetime.datetime.now(datetime.timezone.utc)
                    async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_move):
                        age = (now - entry.created_at).total_seconds()
                        if age > 10:
                            break
                        if not entry.user.bot:
                            moved_by = entry.user
                        break
                except Exception:
                    pass

            if moved_by and moved_by != member:
                title  = "نقل عضو"
                color  = C.WARNING.value
                detail = (f"@المنفذ: {moved_by.mention}\n"
                          f"@العضو: {member.mention}\n"
                          f"من: {before.channel.mention} → إلى: {after.channel.mention}")
            else:
                title  = "تغير الروم"
                color  = C.INFO.value
                detail = f"@العضو: {member.mention}\nمن: {before.channel.mention} → إلى: {after.channel.mention}"
        elif before.mute != after.mute:
            if after.mute:
                title  = "تم كتم العضو صوتياً"
                color  = C.WARNING.value
                detail = after.channel.mention if after.channel else '—'
            else:
                title  = "تم فك كتم العضو صوتياً"
                color  = C.SUCCESS.value
                detail = after.channel.mention if after.channel else '—'
        elif before.deaf != after.deaf:
            if after.deaf:
                title  = "العضو قام بتشغيل الدفن (Deafen)"
                color  = C.GRAPHITE.value
                detail = after.channel.mention if after.channel else '—'
            else:
                title  = "العضو قام بإلغاء الدفن (Undeafen)"
                color  = C.GRAPHITE.value
                detail = after.channel.mention if after.channel else '—'
        else:
            return  # حدث لا نهتم به

        # Send text log instead of embed
        if "نقل" in title:
            # This is a move - extract admin from detail
            log_content = f"""-------------------------------
# لوق روم الفويس
الحدث: {title}
العضو: {member.mention}
من روم: {before.channel.mention if before.channel else '—'}
إلى روم: {after.channel.mention if after.channel else '—'}
-------------------------------"""
        elif "خروج" in title:
            log_content = f"""-------------------------------
# لوق روم الفويس
الحدث: {title}
العضو: {member.mention}
الروم السابق: {detail}
-------------------------------"""
        else:
            log_content = f"""-------------------------------
# لوق روم الفويس
الحدث: {title}
العضو: {member.mention}
الروم: {detail}
-------------------------------"""
        await _smart_log(guild, bd, "voice", log_content)

    async def _apply_auto_mod(self, message: discord.Message, violation: str, detected_content: str = None):
        guild = message.guild
        member = message.author
        if member.bot or member.id == guild.owner_id:
            return
        bot_me = guild.me
        if bot_me and _top_role_pos(bot_me) <= _top_role_pos(member):
            return
        
        bd = self._bot_dir
        p_cfg = _get_punishment_config(bd)
        
        # Check for exempt roles
        exempt_role_ids = p_cfg.get("exempt_role_ids", []) or []
        if exempt_role_ids and any(role.id in exempt_role_ids for role in member.roles):
            return  # User is exempt from auto-mod
        
        # Determine penalty based on new Protection System settings
        action = "timeout"  # Default
        duration_raw = "30m"  # Default
        reason = "مخالفة نظام الحماية"
        
        if violation == "words":
            # Check if specific word penalty is configured
            content_lower = message.content.lower()
            word_penalties = p_cfg.get("word_penalties", {}) or {}
            
            # Find which word triggered the violation
            matched_word = None
            for word in word_penalties.keys():
                if word in content_lower:
                    matched_word = word
                    break
            
            if matched_word and matched_word in word_penalties:
                word_config = word_penalties[matched_word]
                action = word_config.get("type", "timeout")
                duration_raw = word_config.get("duration", "30m")
            else:
                # Fall back to global settings
                action = _normalize_punishment_action(p_cfg.get("action", "timeout"))
                duration_raw = p_cfg.get("duration", "30m")
                
        elif violation == "links":
            # Check if link penalty is configured
            link_penalty = p_cfg.get("link_penalty", {})
            if link_penalty:
                action = link_penalty.get("type", "timeout")
                duration_raw = link_penalty.get("duration", "30m")
            else:
                # Fall back to global settings
                action = _normalize_punishment_action(p_cfg.get("action", "timeout"))
                duration_raw = p_cfg.get("duration", "30m")
        
        dur_secs = _parse_duration_seconds(duration_raw)
        if action != "ban" and dur_secs <= 0:
            dur_secs = 1800  # Default to 30 minutes if invalid
        
        violation_label = "كلمات محظورة" if violation == "words" else "روابط محظورة"
        
        # Dynamic reason with detected content
        if violation == "words" and detected_content:
            reason = f"كلمة محظورة ({detected_content})"
        elif violation == "links" and detected_content:
            reason = f"نشر رابط ({detected_content})"
        else:
            reason = "مخالفة نظام الحماية"
        
        reason_full = f"Auto-Mod ({violation_label}) — {reason}"
        
        try:
            await message.delete()
        except Exception:
            pass
        
        try:
            await member.send(f"تم رصد مخالفة في سيرفر {guild.name} | السبب: {reason} | النوع: {violation_label} | العقوبة: {_punishment_label(action)}")
        except Exception:
            pass
        
        log_content = f"""-------------------------------
# لوق الحماية التلقائية
العضو: {member.mention}
النوع: {violation_label}
العقوبة: {_punishment_label(action)}
المدة: {_format_duration(dur_secs) if action != 'ban' or dur_secs > 0 else 'دائم'}
السبب: {reason}
-------------------------------"""
        
        if bool(cfg("feature_sanctions", bd)):
            await _smart_log(guild, bd, "sanctions", log_content)
        
        if action == "ban":
            await member.ban(reason=reason_full, delete_message_days=0)
            if dur_secs > 0:
                async def _auto_unban():
                    await asyncio.sleep(dur_secs)
                    try:
                        await guild.unban(discord.Object(id=member.id), reason="انتهى الباند المؤقت (Auto-Mod)")
                    except Exception:
                        pass
                asyncio.create_task(_auto_unban())
        else:
            until = discord.utils.utcnow() + datetime.timedelta(seconds=dur_secs)
            await member.timeout(until, reason=reason_full)

    # ── محرك الأوامر النصية المخصصة (on_message) ─────────────────────────────
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        if not self._guild_ok(message.guild.id):
            return

        content = message.content.strip()
        # Check if message has any content type that should trigger processing
        has_content = bool(content) or bool(message.attachments) or bool(message.stickers) or bool(message.embeds)
        if not has_content:
            return

        bd       = self._bot_dir
        cmd_data = get_cmd_cfg(bd)
        guild    = message.guild
        author   = message.author
        content_lower = content.lower() if content else ""

        # ── نظام الحماية Auto-Mod ─────────────────────────────────────────
        if bool(cfg("feature_auto_mod", bd)) and content:
            patterns = self._prohibited_word_patterns or []
            links = (self.punishment_config or {}).get("link_prefixes", []) or []
            word_hit = False
            detected_word = None
            if patterns:
                for pat in patterns:
                    if isinstance(pat, str):
                        if pat in content_lower:
                            word_hit = True
                            detected_word = pat
                            break
                    else:
                        if pat.search(content_lower):
                            word_hit = True
                            # For regex patterns, try to find the actual matched word
                            match = pat.search(content_lower)
                            if match:
                                detected_word = match.group(0)
                            else:
                                detected_word = str(pat.pattern)
                            break
            link_hit = False
            detected_link = None
            if not word_hit and links:
                for prefix in links:
                    if prefix in content_lower:
                        link_hit = True
                        detected_link = prefix
                        break
            if word_hit or link_hit:
                await self._apply_auto_mod(message, "words" if word_hit else "links", detected_word if word_hit else detected_link)
                return

        # ── محرك الرد التلقائي ─────────────────────────────────────────────
        # Always active - no feature toggle needed
        if content:
            ar_data = _get_auto_responses(bd)
            for kw, reply_text in ar_data.items():
                if kw in content_lower:
                    try:
                        await message.reply(reply_text, mention_author=True)
                    except Exception:
                        pass
                    return  # رد واحد فقط

        # ── نظام الفواصل (Separators) ───────────────────────────────────────
        await system_extensions.handle_separator_post(message, bd)

        # ── نظام المسؤولين (Feature Managers) ─────────────────────────────
        await system_extensions.handle_manager_shortcut(message, self)

        # ── نظام نظام الرياكشن (Reaction Room Unlock) ─────────────────
        if bool(cfg("feature_reaction_room", bd)):
            rr_ch_id = cfg("reaction_room_channel", bd)
            rr_writer_role_id = cfg("reaction_room_writer_role", bd)
            rr_emoji = cfg("reaction_room_emoji", bd)
            
            if rr_ch_id and rr_writer_role_id and rr_emoji:
                if message.channel.id == int(rr_ch_id):
                    writer_role = guild.get_role(int(rr_writer_role_id))
                    if writer_role and writer_role in author.roles:
                        # Writer posted in reaction room - trigger unlock sequence
                        # Backup all existing members' roles (excluding bots and Writer Role)
                        backup_data = {}
                        for member in guild.members:
                            if member.bot or writer_role in member.roles:
                                continue
                            role_ids = [r.id for r in member.roles if not r.is_default() and not r.managed]
                            if role_ids:
                                backup_data[str(member.id)] = role_ids
                        
                        # Save backup to config
                        set_cfg("reaction_room_backup", backup_data, bd)
                        set_cfg("reaction_room_message_id", message.id, bd)
                        
                        # Strip all roles from backed-up members
                        for member_id_str, role_ids in backup_data.items():
                            member = guild.get_member(int(member_id_str))
                            if member:
                                removable_roles = [r for r in member.roles if not r.is_default() and not r.managed]
                                if removable_roles:
                                    try:
                                        await member.remove_roles(*removable_roles, reason="قفل السيرفر - نظام الرياكشن")
                                    except Exception:
                                        pass
                        
                        # Add emoji reaction to the message
                        try:
                            await message.add_reaction(rr_emoji)
                        except Exception:
                            pass
                        
                        print(f"[SystemBot] 🔓 Reaction Room unlock triggered by {author.display_name} in {message.channel.name}")

        # ── أمر رولي (لأصحاب الرول الخاص) ───────────────────────────────────
        if content and content_lower in ["رولي", "!رولي"]:
            bd = self._bot_dir
            user_roles = cfg("user_roles", bd) or {}
            custom_roles = cfg("custom_roles", bd) or {}
            
            target_role = None
            target_role_id = None
            
            # Check user_roles database (direct mapping: user_id -> role_id)
            role_id_str = user_roles.get(str(author.id))
            if role_id_str:
                role = guild.get_role(int(role_id_str))
                if role:
                    target_role = role
                    target_role_id = role_id_str
            
            # Fallback: check if user has any custom role from their active roles
            if not target_role:
                for role in author.roles:
                    if str(role.id) in custom_roles:
                        role_data = custom_roles[str(role.id)]
                        if str(author.id) == str(role_data.get("owner_id")):
                            target_role = role
                            target_role_id = str(role.id)
                            break
            
            if target_role:
                await message.reply(
                    f"{author.mention} تعديل رولي:",
                    view=CustomRoleControlView(self, guild, target_role, author),
                    embeds=[]
                )
            else:
                await message.reply(f"{author.mention} ليس لديك رول خاص مسجل باسمك.", embeds=[])
            return

        # ── أمر الاقتباس (") — حذف رومات جماعي ──────────────────────────────
        if content and content == '"':
            await self._mass_delete_channels_cmd(message)
            return

        # ── مطابقة الاسم المخصص والأسماء البديلة ─────────────────────────────
        matched_action = None
        matched_args   = ""
        if content:
            for action, entry in cmd_data.items():
                cmd_name = entry.get("name", "").strip()
                if not cmd_name:
                    continue
                # جمع الاسم الأساسي + كل الأسماء البديلة
                all_names = [cmd_name] + [a.strip() for a in entry.get("aliases", []) if a.strip()]
                for name_variant in all_names:
                    if not name_variant:
                        continue
                    if content_lower.startswith(name_variant.lower()):
                        rest = content[len(name_variant):].strip()
                        matched_action = action
                        matched_args   = rest
                        break
                if matched_action:
                    break

        if not matched_action:
            return

        entry = cmd_data[matched_action]

        # ── فحص الصلاحيات ──────────────────────────────────────────────────
        # Apply strict permission check for ALL commands including give_role
        if not _cmd_allowed(author, matched_action, bd):
            return  # Ignore unauthorized users completely

        # ── استخراج المنشن أو ID ────────────────────────────────────────────
        async def _get_target_from_args(args: str):
            if not args:
                return None, ""
            # منشن أو ID
            raw = args.split()[0]
            raw = raw.strip("<@!>")
            try:
                uid = int(raw)
                m = guild.get_member(uid)
                if not m:
                    try: m = await guild.fetch_member(uid)
                    except: pass
                # Remove the target mention from args
                remaining_args = args.split(maxsplit=1)[1] if len(args.split()) > 1 else ""
                return m, remaining_args
            except ValueError:
                return None, args

        # ── Reply-to-Message target detection ─────────────────────────────────
        target = None
        remaining_args = matched_args
        if message.reference and message.reference.message_id:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                target = ref_msg.author
                # When replying, the entire matched_args is the argument
                remaining_args = matched_args
            except Exception:
                pass
        
        # Fallback to mention/ID if no reply target
        if not target:
            target, remaining_args = await _get_target_from_args(matched_args)

        # ── فحص Hierarchy ──────────────────────────────────────────────────
        sanction_actions = {
            "kick","ban","tempban","timeout","untimeout","warn","mute_chat","mute","strip_roles",
            "unmute","unmute_chat","jail","unjail"
        }
        utility_actions = {
            "move","disconnect","nick","give_role","take_role",
            "userinfo","whois","deafen","undeafen"
        }
        actions_needing_target = sanction_actions | utility_actions
        
        # Target missing handler (excluding channel-only commands)
        if matched_action in actions_needing_target and not target:
            try:
                await message.reply("حدد عضو")
            except discord.HTTPException:
                pass  # Message was deleted, ignore error
            return
        
        if matched_action in actions_needing_target and target:
            # فحص الاستهداف الذاتي
            if target.id == author.id:
                return
            # فحص التسلسل الهرمي للعقوبات فقط
            if matched_action in sanction_actions:
                if target.top_role.position >= author.top_role.position:
                    try:
                        await message.reply("هادا شخص اعلا منك")
                    except discord.HTTPException:
                        pass  # Message was deleted, ignore error
                    return

        # ── تنفيذ الأوامر ──────────────────────────────────────────────────
        async def _add_success_reaction():
            try:
                await message.add_reaction("✅")
            except Exception:
                pass

        def _find_role(role_identifier: str):
            """Smart role lookup by mention, ID, or name"""
            # Check role mentions first
            if message.role_mentions:
                return message.role_mentions[0]
            
            # Try ID
            try:
                rid = int(role_identifier.strip("<@&>"))
                role = guild.get_role(rid)
                if role:
                    return role
            except ValueError:
                pass
            
            # Try exact name match (case-insensitive)
            role_identifier_lower = role_identifier.lower().strip()
            for role in guild.roles:
                if role.name.lower() == role_identifier_lower:
                    return role
            
            # Try partial name match
            for role in guild.roles:
                if role_identifier_lower in role.name.lower():
                    return role
            
            return None

        async def _add_success_reaction():
            try:
                await message.add_reaction("✅")
            except Exception:
                pass

        try:
            # ────── قائمة الأوامر ──────
            if matched_action in {"اوامر", "أوامر", "commands", "help"}:
                commands_list = [
                    ("=kick @member", "👢 طرد عضو"),
                    ("=ban @member", "🔨 باند نهائي"),
                    ("=tempban @member [duration]", "⏳ باند مؤقت"),
                    ("=timeout @member [duration]", "⏱️ سجن مؤقت"),
                    ("=warn @member [reason]", "⚠️ تحذير"),
                    ("=mute_chat @member [duration]", "🔇 كتم شات"),
                    ("=mute @member", "🔕 كتم صوت"),
                    ("=strip_roles @member", "✂️ سحب رتب"),
                    ("=nick @member new_name", "✏️ تغيير اسم"),
                    ("=clear N", "🧹 مسح رسائل"),
                    ("=lock", "🔒 قفل القناة"),
                    ("=unlock", "🔓 فتح القناة"),
                    ("=slowmode [seconds]", "🐢 بطء"),
                    ("=hide", "🙈 إخفاء القناة"),
                    ("=show", "👁️ إظهار القناة"),
                ]
                e = _embed("📜 قائمة الأوامر", "جميع الأوامر المتاحة:\n\n" + "\n".join([f"`{cmd}` - {desc}" for cmd, desc in commands_list]), C.INFO)
                await message.reply(embed=e)
                return

            # ────── العقوبات ──────
            if matched_action == "kick":
                if not target: return
                await target.kick(reason=f"طرد بأمر {author.display_name}")
                await _add_success_reaction()
                await _smart_log(guild, bd, "admin",
                    _embed("👢 طرد", f"المنفذ: {author.mention}\nالهدف: {target.mention}", C.WARNING,
                           footer=f"System Bot  •  on_message  •  {_now_str()}"))

            elif matched_action == "ban":
                if not target: return
                
                # Apply initial ban
                await target.ban(reason=f"باند بأمر {author.display_name}", delete_message_days=0)
                
                # Create revert function
                async def revert_ban():
                    try:
                        await guild.unban(discord.Object(id=target.id), reason="انتهت مدة الاختيار")
                    except Exception:
                        pass
                
                # Send select menu with plain text
                select_view = SanctionSelectView(self, message, target, "باند", author, revert_ban, bd)
                menu_msg = await message.reply(
                    f"{author.mention} اختر السبب والمدة:",
                    view=select_view
                )
                # Track pending sanction
                self._pending_sanctions[message.id] = {
                    "target": target,
                    "sanction_type": "باند",
                    "revert_func": revert_ban,
                    "bot_dir": bd,
                    "menu_msg": menu_msg
                }

            elif matched_action == "tempban":
                if not target: return
                
                # Apply initial ban
                parts = matched_args.split()
                dur_secs = DEFAULT_TEMPBAN_SECONDS
                if len(parts) >= 2:
                    parsed = _parse_duration_seconds(parts[1])
                    if parsed > 0:
                        dur_secs = parsed
                dur_str = _format_duration(dur_secs)
                await target.ban(reason=f"باند مؤقت {dur_str}", delete_message_days=0)
                
                # Create revert function
                async def revert_tempban():
                    try:
                        await guild.unban(discord.Object(id=target.id), reason="انتهت مدة الاختيار")
                    except Exception:
                        pass
                
                # Send select menu with plain text
                select_view = SanctionSelectView(self, message, target, "باند مؤقت", author, revert_tempban, bd)
                menu_msg = await message.reply(
                    f"{author.mention} اختر السبب والمدة:",
                    view=select_view
                )
                # Track pending sanction
                self._pending_sanctions[message.id] = {
                    "target": target,
                    "sanction_type": "باند مؤقت",
                    "revert_func": revert_tempban,
                    "bot_dir": bd,
                    "menu_msg": menu_msg
                }

            elif matched_action == "timeout":
                if not target: return
                
                # Apply initial timeout (temporary - 1 minute default for selection)
                parts = matched_args.split()
                dur_secs = 3600
                if len(parts) >= 2:
                    parsed = _parse_duration_seconds(parts[1])
                    if parsed > 0:
                        dur_secs = parsed
                dur_secs = min(dur_secs, MAX_TIMEOUT_SECONDS)
                dur_str = _format_duration(dur_secs)
                until = discord.utils.utcnow() + datetime.timedelta(seconds=dur_secs)
                
                # Backup user's current roles before timeout
                saved_roles = save_muted_user_roles(target, bd)
                
                # Remove all active roles (except @everyone, managed, and above bot) and apply timeout
                bot_top_role = guild.me.top_role if guild.me else None
                removable_roles = []
                for r in target.roles:
                    if r.is_default() or r.managed:
                        continue
                    if bot_top_role and r.position >= bot_top_role.position:
                        continue
                    removable_roles.append(r)
                
                if removable_roles:
                    try:
                        await target.remove_roles(*removable_roles, reason="سجن مؤقت - حفظ الرتب")
                    except discord.Forbidden:
                        print(f"[SystemBot] ⚠️ Cannot remove roles for {target.display_name} - hierarchy check failed")
                    except discord.HTTPException as e:
                        print(f"[SystemBot] ⚠️ HTTP error removing roles for {target.display_name}: {e}")
                
                await target.timeout(until, reason=f"سجن بأمر {author.display_name}")
                
                # Create revert function that restores roles
                async def revert_timeout():
                    try:
                        # FIRST: Restore saved roles BEFORE removing timeout
                        saved_role_ids = load_muted_user_roles(target.id, bd)
                        roles_to_restore = []
                        for rid in saved_role_ids:
                            role_obj = guild.get_role(rid)
                            if role_obj and role_obj < guild.me.top_role:  # ensure bot has hierarchy permission
                                roles_to_restore.append(role_obj)
                        
                        if roles_to_restore:
                            print(f"[DEBUG] timeout revert: Restoring roles for {target.name}: {[r.name for r in roles_to_restore]}")
                            try:
                                await target.add_roles(*roles_to_restore, reason="استعادة الرتب بعد انتهاء السجن")
                            except discord.Forbidden:
                                print(f"[SystemBot] ⚠️ Cannot restore roles for {target.display_name} - hierarchy check failed")
                            except discord.HTTPException as e:
                                print(f"[SystemBot] ⚠️ HTTP error restoring roles for {target.display_name}: {e}")
                        
                        # SECOND: Remove timeout
                        await target.timeout(None, reason="انتهت مدة الاختيار")
                        
                        # THIRD: Clear saved roles from backup
                        clear_muted_user_roles(target.id, bd)
                    except Exception as e:
                        print(f"[SystemBot] Error in timeout revert for {target.display_name}: {e}")
                
                # Send select menu with plain text
                select_view = SanctionSelectView(self, message, target, "سجن مؤقت", author, revert_timeout, bd)
                menu_msg = await message.reply(
                    f"{author.mention} اختر السبب والمدة:",
                    view=select_view
                )
                # Track pending sanction
                self._pending_sanctions[message.id] = {
                    "target": target,
                    "sanction_type": "سجن مؤقت",
                    "revert_func": revert_timeout,
                    "bot_dir": bd,
                    "menu_msg": menu_msg
                }

            elif matched_action == "warn":
                if not target: return
                reason = " ".join(matched_args.split()[1:]) or "مخالفة إدارية"
                try:
                    await target.send(embed=_embed("⚠️ تحذير",
                        f"تلقيت تحذيراً في **{guild.name}**\n"
                        f"من: {author.mention}\nالسبب: {reason}", C.WARNING))
                except: pass
                await _add_success_reaction()

            elif matched_action == "mute_chat":
                if not target: return
                mute_role_id = cfg("mute_role", bd)
                if not mute_role_id:
                    await message.reply("❌ لم يتم تعيين رول الكتم. يرجى ضبطه من إعدادات العقوبات.")
                    return
                mute_role = guild.get_role(int(mute_role_id))
                if not mute_role:
                    await message.reply("❌ رول الكتم غير موجود. يرجى ضبطه من إعدادات العقوبات.")
                    return
                if mute_role in target.roles:
                    await message.reply("⚠️ العضو مكتوم بالفعل.")
                    return

                # Parse duration
                parts = matched_args.split()
                dur_secs = 0
                if len(parts) >= 2:
                    parsed = _parse_duration_seconds(parts[1])
                    if parsed > 0:
                        dur_secs = parsed

                # IMMEDIATELY Backup user's current roles BEFORE any action
                saved_roles = save_muted_user_roles(target, bd)

                # Remove all active roles (except @everyone, managed, and above bot) and assign only mute role
                bot_top_role = guild.me.top_role if guild.me else None
                removable_roles = []
                for r in target.roles:
                    if r.is_default() or r.managed:
                        continue
                    if bot_top_role and r.position >= bot_top_role.position:
                        continue
                    removable_roles.append(r)
                
                if removable_roles:
                    try:
                        await target.remove_roles(*removable_roles, reason="كتم شات - حفظ الرتب")
                    except discord.Forbidden:
                        print(f"[SystemBot] ⚠️ Cannot remove roles for {target.display_name} - hierarchy check failed")
                    except discord.HTTPException as e:
                        print(f"[SystemBot] ⚠️ HTTP error removing roles for {target.display_name}: {e}")
                
                try:
                    await target.add_roles(mute_role, reason="كتم شات بأمر")
                except discord.Forbidden:
                    print(f"[SystemBot] ⚠️ Cannot add mute role to {target.display_name} - hierarchy check failed")
                except discord.HTTPException as e:
                    print(f"[SystemBot] ⚠️ HTTP error adding mute role to {target.display_name}: {e}")
                
                # Create revert function that restores roles
                async def revert_mute():
                    try:
                        # FIRST: Restore saved roles BEFORE removing mute role
                        saved_role_ids = load_muted_user_roles(target.id, bd)
                        roles_to_restore = []
                        for rid in saved_role_ids:
                            role_obj = guild.get_role(rid)
                            if role_obj and role_obj < guild.me.top_role:  # ensure bot has hierarchy permission
                                roles_to_restore.append(role_obj)
                        
                        if roles_to_restore:
                            print(f"[DEBUG] mute revert: Restoring roles for {target.name}: {[r.name for r in roles_to_restore]}")
                            try:
                                await target.add_roles(*roles_to_restore, reason="استعادة الرتب بعد انتهاء الكتم")
                            except discord.Forbidden:
                                print(f"[SystemBot] ⚠️ Cannot restore roles for {target.display_name} - hierarchy check failed")
                            except discord.HTTPException as e:
                                print(f"[SystemBot] ⚠️ HTTP error restoring roles for {target.display_name}: {e}")
                        
                        # SECOND: Remove mute role
                        try:
                            await target.remove_roles(mute_role, reason="انتهت مدة الاختيار")
                        except discord.Forbidden:
                            print(f"[SystemBot] ⚠️ Cannot remove mute role from {target.display_name} - hierarchy check failed")
                        except discord.HTTPException as e:
                            print(f"[SystemBot] ⚠️ HTTP error removing mute role from {target.display_name}: {e}")
                        
                        # THIRD: Clear saved roles from backup
                        clear_muted_user_roles(target.id, bd)
                    except Exception as e:
                        print(f"[SystemBot] Error in mute revert for {target.display_name}: {e}")

                # If duration specified, schedule auto-unmute
                if dur_secs > 0:
                    dur_str = _format_duration(dur_secs)
                    async def _auto_unmute():
                        await asyncio.sleep(dur_secs)
                        try:
                            await revert_mute()
                            log_restore = _embed("✅ انتهت مدة الكتم",
                                f"تم فك الكتم عن {target.mention}\n"
                                f"انتهت المدة: {dur_str}\n"
                                f"تم استعادة الرتب المحفوظة", C.SUCCESS,
                                footer=f"System Bot  •  Auto-Unmute  •  {_now_str()}")
                            await _smart_log(guild, bd, "admin", log_restore)
                        except Exception:
                            pass
                    asyncio.create_task(_auto_unmute())

                # Send select menu with plain text
                select_view = SanctionSelectView(self, message, target, "كتم شات", author, revert_mute, bd)
                menu_msg = await message.reply(
                    f"{author.mention} اختر السبب والمدة:",
                    view=select_view
                )
                # Track pending sanction
                self._pending_sanctions[message.id] = {
                    "target": target,
                    "sanction_type": "كتم شات",
                    "revert_func": revert_mute,
                    "bot_dir": bd,
                    "menu_msg": menu_msg
                }

            elif matched_action == "mute":
                if not target: return
                await target.edit(mute=True, reason="كتم صوت")
                await _add_success_reaction()

            elif matched_action == "strip_roles":
                if not target: return
                bot_top_role = guild.me.top_role if guild.me else None
                removable = []
                for r in target.roles:
                    if r.is_default() or r.managed:
                        continue
                    if bot_top_role and r.position >= bot_top_role.position:
                        continue
                    removable.append(r)
                if removable:
                    try:
                        await target.remove_roles(*removable, reason="سحب كل الرتب")
                    except discord.Forbidden:
                        print(f"[SystemBot] ⚠️ Cannot strip roles for {target.display_name} - hierarchy check failed")
                    except discord.HTTPException as e:
                        print(f"[SystemBot] ⚠️ HTTP error stripping roles for {target.display_name}: {e}")
                await _add_success_reaction()

            elif matched_action == "lock":
                ch = message.channel
                await ch.set_permissions(guild.default_role, send_messages=False)
                await _add_success_reaction()

            elif matched_action == "unlock":
                ch = message.channel
                await ch.set_permissions(guild.default_role, send_messages=True)
                await _add_success_reaction()

            elif matched_action == "hide":
                ch = message.channel
                await ch.set_permissions(guild.default_role, view_channel=False)
                await _add_success_reaction()

            elif matched_action == "show":
                ch = message.channel
                await ch.set_permissions(guild.default_role, view_channel=True)
                await _add_success_reaction()

            elif matched_action == "clear":
                parts = matched_args.split()
                n = 10
                if parts:
                    try: n = max(1, min(100, int(parts[0])))
                    except: pass
                deleted = await message.channel.purge(limit=n + 1)
                try:
                    confirm = await message.reply(
                        embed=_embed("🧹 تم", f"حُذفت **{len(deleted)}** رسالة.", C.SUCCESS))
                    await asyncio.sleep(4)
                    await confirm.delete()
                except: pass

            elif matched_action == "slowmode":
                parts = matched_args.split()
                secs  = 0
                if parts:
                    try: secs = max(0, min(21600, int(parts[0])))
                    except: pass
                await message.channel.edit(slowmode_delay=secs)
                await _add_success_reaction()

            elif matched_action == "move":
                # move @target VoiceChannelID  — أو يسحب للروم الذي فيه الأونر
                if not target: return
                parts    = remaining_args.split()
                # ابحث عن VoiceChannel ID في الـ args
                dst = None
                for p in parts:
                    try:
                        c = guild.get_channel(int(p))
                        if c and isinstance(c, discord.VoiceChannel):
                            dst = c; break
                    except: pass
                # إذا لم يذكر، اسحب لروم الأونر الصوتي
                if not dst and author.voice:
                    dst = author.voice.channel
                if not dst:
                    return
                import time as _time
                self._pending_voice_actions[target.id] = {"executor": author, "action": "move", "ts": _time.time()}
                await target.move_to(dst, reason=f"سحب بأمر {author.display_name}")
                await _add_success_reaction()

            elif matched_action == "move_all":
                # move_all SourceID DestID
                parts = matched_args.split()  # Use original args for move_all
                if len(parts) < 2:
                    return
                try:
                    src = guild.get_channel(int(parts[0]))
                    dst = guild.get_channel(int(parts[1]))
                    if not src or not isinstance(src, discord.VoiceChannel):
                        return
                    if not dst or not isinstance(dst, discord.VoiceChannel):
                        return
                    count = 0
                    for m in list(src.members):
                        try: await m.move_to(dst); count += 1
                        except: pass
                    await _add_success_reaction()
                except ValueError:
                    pass

            elif matched_action == "disconnect":
                if not target: return
                import time as _time
                self._pending_voice_actions[target.id] = {"executor": author, "action": "disconnect", "ts": _time.time()}
                await target.move_to(None, reason="فصل صوتي")
                await _add_success_reaction()

            elif matched_action == "nick":
                if not target: return
                new_name = remaining_args or None
                await target.edit(nick=new_name)
                await _add_success_reaction()

            elif matched_action == "give_role":
                if not target: return
                if not remaining_args:
                    await message.reply("حدد الرتبة")
                    return
                role = _find_role(remaining_args)
                if not role:
                    await message.reply("لم يتم العثور على الرتبة")
                    return
                try:
                    await target.add_roles(role)
                except discord.Forbidden:
                    print(f"[SystemBot] ⚠️ Cannot add role to {target.display_name} - hierarchy check failed")
                except discord.HTTPException as e:
                    print(f"[SystemBot] ⚠️ HTTP error adding role to {target.display_name}: {e}")
                await _add_success_reaction()

            elif matched_action == "take_role":
                if not target: return
                if not remaining_args:
                    await message.reply("حدد الرتبة")
                    return
                role = _find_role(remaining_args)
                if not role:
                    await message.reply("لم يتم العثور على الرتبة")
                    return
                try:
                    await target.remove_roles(role)
                except discord.Forbidden:
                    print(f"[SystemBot] ⚠️ Cannot remove role from {target.display_name} - hierarchy check failed")
                except discord.HTTPException as e:
                    print(f"[SystemBot] ⚠️ HTTP error removing role from {target.display_name}: {e}")
                await _add_success_reaction()

            elif matched_action == "unmute":
                if not target: return
                
                # FIRST: Restore saved roles from backup BEFORE removing mute role
                saved_role_ids = load_muted_user_roles(target.id, bd)
                roles_to_restore = []
                for rid in saved_role_ids:
                    role_obj = guild.get_role(rid)
                    if role_obj and role_obj < guild.me.top_role:  # ensure bot has hierarchy permission
                        roles_to_restore.append(role_obj)
                
                if roles_to_restore:
                    print(f"[DEBUG] unmute cmd: Restoring roles for {target.name}: {[r.name for r in roles_to_restore]}")
                    try:
                        await target.add_roles(*roles_to_restore, reason="استعادة الرتب بعد فك الكتم")
                    except discord.Forbidden:
                        print(f"[SystemBot] ⚠️ Cannot restore roles for {target.display_name} - hierarchy check failed")
                    except discord.HTTPException as e:
                        print(f"[SystemBot] ⚠️ HTTP error restoring roles for {target.display_name}: {e}")
                
                # SECOND: Remove the Mute role
                mute_role_id = cfg("mute_role", bd)
                if mute_role_id:
                    mute_role = guild.get_role(int(mute_role_id))
                    if mute_role and mute_role in target.roles:
                        try:
                            await target.remove_roles(mute_role, reason="فك كتم صوت")
                        except discord.Forbidden:
                            print(f"[SystemBot] ⚠️ Cannot remove mute role from {target.display_name} - hierarchy check failed")
                        except discord.HTTPException as e:
                            print(f"[SystemBot] ⚠️ HTTP error removing mute role from {target.display_name}: {e}")
                
                # THIRD: Clear saved roles from backup
                clear_muted_user_roles(target.id, bd)
                
                await target.edit(mute=False)
                await _add_success_reaction()
                await _smart_log(guild, bd, "admin",
                    _embed("🔊 فك كتم صوت", f"المنفذ: {author.mention}\nالهدف: {target.mention}", C.SUCCESS,
                           footer=f"System Bot  •  on_message  •  {_now_str()}"))

            elif matched_action == "unmute_chat":
                if not target: return
                
                # FIRST: Restore saved roles from backup BEFORE removing mute role
                saved_role_ids = load_muted_user_roles(target.id, bd)
                roles_to_restore = []
                for rid in saved_role_ids:
                    role_obj = guild.get_role(rid)
                    if role_obj and role_obj < guild.me.top_role:  # ensure bot has hierarchy permission
                        roles_to_restore.append(role_obj)
                
                if roles_to_restore:
                    print(f"[DEBUG] unmute_chat cmd: Restoring roles for {target.name}: {[r.name for r in roles_to_restore]}")
                    try:
                        await target.add_roles(*roles_to_restore, reason="استعادة الرتب بعد فك الكتم")
                    except discord.Forbidden:
                        print(f"[SystemBot] ⚠️ Cannot restore roles for {target.display_name} - hierarchy check failed")
                    except discord.HTTPException as e:
                        print(f"[SystemBot] ⚠️ HTTP error restoring roles for {target.display_name}: {e}")
                
                # SECOND: Remove the Mute role
                mute_role_id = cfg("mute_role", bd)
                if mute_role_id:
                    mute_role = guild.get_role(int(mute_role_id))
                    if mute_role and mute_role in target.roles:
                        try:
                            await target.remove_roles(mute_role, reason="فك كتم شات")
                        except discord.Forbidden:
                            print(f"[SystemBot] ⚠️ Cannot remove mute role from {target.display_name} - hierarchy check failed")
                        except discord.HTTPException as e:
                            print(f"[SystemBot] ⚠️ HTTP error removing mute role from {target.display_name}: {e}")
                
                # THIRD: Clear saved roles from backup
                clear_muted_user_roles(target.id, bd)
                
                await target.timeout(None)
                await _add_success_reaction()
                await _smart_log(guild, bd, "admin",
                    _embed("💬 فك كتم شات", f"المنفذ: {author.mention}\nالهدف: {target.mention}", C.SUCCESS,
                           footer=f"System Bot  •  on_message  •  {_now_str()}"))

            elif matched_action == "untimeout":
                if not target: return
                
                # FIRST: Restore saved roles from backup BEFORE removing timeout
                saved_role_ids = load_muted_user_roles(target.id, bd)
                roles_to_restore = []
                for rid in saved_role_ids:
                    role_obj = guild.get_role(rid)
                    if role_obj and role_obj < guild.me.top_role:  # ensure bot has hierarchy permission
                        roles_to_restore.append(role_obj)
                
                if roles_to_restore:
                    print(f"[DEBUG] untimeout cmd: Restoring roles for {target.name}: {[r.name for r in roles_to_restore]}")
                    try:
                        await target.add_roles(*roles_to_restore, reason="استعادة الرتب بعد فك السجن")
                    except discord.Forbidden:
                        print(f"[SystemBot] ⚠️ Cannot restore roles for {target.display_name} - hierarchy check failed")
                    except discord.HTTPException as e:
                        print(f"[SystemBot] ⚠️ HTTP error restoring roles for {target.display_name}: {e}")
                
                # SECOND: Remove timeout
                await target.timeout(None, reason=f"فك سجن بأمر {author.display_name}")
                
                # THIRD: Clear saved roles from backup
                clear_muted_user_roles(target.id, bd)
                
                await _add_success_reaction()
                await _smart_log(guild, bd, "admin",
                    _embed("🕊️ فك سجن", f"المنفذ: {author.mention}\nالهدف: {target.mention}", C.SUCCESS,
                           footer=f"System Bot  •  on_message  •  {_now_str()}"))

            elif matched_action == "jail":
                jail_role_id = cfg("jail_role_id", bd)
                if not jail_role_id:
                    await message.reply("❌ لم يتم تعيين رول السجن. يرجى ضبطه من إعدادات العقوبات.")
                    return
                jail_role = guild.get_role(int(jail_role_id))
                if not jail_role:
                    await message.reply("❌ رول السجن غير موجود. يرجى ضبطه من إعدادات العقوبات.")
                    return
                if jail_role in target.roles:
                    await message.reply("⚠️ العضو مسجون بالفعل.")
                    return
                
                # Parse duration
                parts = matched_args.split()
                dur_secs = 0
                if len(parts) >= 2:
                    parsed = _parse_duration_seconds(parts[1])
                    if parsed > 0:
                        dur_secs = parsed
                
                # Backup user's current roles before jailing
                saved_roles = save_jailed_user_roles(target, bd)
                
                # Apply initial jail role (with hierarchy checking)
                bot_top_role = guild.me.top_role if guild.me else None
                removable_roles = []
                for r in target.roles:
                    if r.is_default() or r.managed:
                        continue
                    if bot_top_role and r.position >= bot_top_role.position:
                        continue
                    removable_roles.append(r)
                
                if removable_roles:
                    try:
                        await target.remove_roles(*removable_roles, reason=f"{self.JAIL_ACTION_NAME} - حفظ الرتب")
                    except discord.Forbidden:
                        print(f"[SystemBot] ⚠️ Cannot remove roles for {target.display_name} - hierarchy check failed")
                    except discord.HTTPException as e:
                        print(f"[SystemBot] ⚠️ HTTP error removing roles for {target.display_name}: {e}")
                
                try:
                    await target.add_roles(jail_role, reason=f"{self.JAIL_ACTION_NAME} بأمر")
                except discord.Forbidden:
                    print(f"[SystemBot] ⚠️ Cannot add jail role to {target.display_name} - hierarchy check failed")
                except discord.HTTPException as e:
                    print(f"[SystemBot] ⚠️ HTTP error adding jail role to {target.display_name}: {e}")
                
                # Create revert function that restores roles
                async def revert_jail():
                    try:
                        # FIRST: Restore saved roles BEFORE removing jail role
                        saved_role_ids = load_jailed_user_roles(target.id, bd)
                        roles_to_restore = []
                        for rid in saved_role_ids:
                            role_obj = guild.get_role(rid)
                            if role_obj and role_obj < guild.me.top_role:  # ensure bot has hierarchy permission
                                roles_to_restore.append(role_obj)
                        
                        if roles_to_restore:
                            print(f"[DEBUG] jail revert: Restoring roles for {target.name}: {[r.name for r in roles_to_restore]}")
                            try:
                                await target.add_roles(*roles_to_restore, reason="استعادة الرتب بعد انتهاء السجن")
                            except discord.Forbidden:
                                print(f"[SystemBot] ⚠️ Cannot restore roles for {target.display_name} - hierarchy check failed")
                            except discord.HTTPException as e:
                                print(f"[SystemBot] ⚠️ HTTP error restoring roles for {target.display_name}: {e}")
                        
                        # SECOND: Remove jail role
                        try:
                            await target.remove_roles(jail_role, reason="انتهت مدة الاختيار")
                        except discord.Forbidden:
                            print(f"[SystemBot] ⚠️ Cannot remove jail role from {target.display_name} - hierarchy check failed")
                        except discord.HTTPException as e:
                            print(f"[SystemBot] ⚠️ HTTP error removing jail role from {target.display_name}: {e}")
                        
                        # THIRD: Clear saved roles from backup
                        clear_jailed_user_roles(target.id, bd)
                    except Exception as e:
                        print(f"[SystemBot] Error in jail revert for {target.display_name}: {e}")
                
                # If duration specified, schedule auto-unjail
                if dur_secs > 0:
                    dur_str = _format_duration(dur_secs)
                    async def _auto_unjail():
                        await asyncio.sleep(dur_secs)
                        try:
                            await revert_jail()
                            log_restore = _embed("✅ انتهت مدة السجن",
                                f"تم إخراج {target.mention} من السجن\n"
                                f"انتهت المدة: {dur_str}\n"
                                f"تم استعادة الرتب المحفوظة", C.SUCCESS,
                                footer=f"System Bot  •  Auto-Unjail  •  {_now_str()}")
                            await _smart_log(guild, bd, "admin", log_restore)
                        except Exception:
                            pass
                    asyncio.create_task(_auto_unjail())
                
                # Send select menu with plain text
                select_view = SanctionSelectView(self, message, target, self.JAIL_CUSTOM_TITLE, author, revert_jail, bd)
                menu_msg = await message.reply(
                    f"{author.mention} اختر السبب والمدة:",
                    view=select_view
                )
                # Track pending sanction
                self._pending_sanctions[message.id] = {
                    "target": target,
                    "sanction_type": self.JAIL_CUSTOM_TITLE,
                    "revert_func": revert_jail,
                    "bot_dir": bd,
                    "menu_msg": menu_msg
                }

            elif matched_action == "unjail":
                if not target: return
                
                # FIRST: Restore saved roles BEFORE removing jail role
                saved_role_ids = load_jailed_user_roles(target.id, bd)
                roles_to_restore = []
                for rid in saved_role_ids:
                    role_obj = guild.get_role(rid)
                    if role_obj and role_obj < guild.me.top_role:  # ensure bot has hierarchy permission
                        roles_to_restore.append(role_obj)
                
                if roles_to_restore:
                    print(f"[DEBUG] unjail cmd: Restoring roles for {target.name}: {[r.name for r in roles_to_restore]}")
                    try:
                        await target.add_roles(*roles_to_restore, reason=f"استعادة الرتب بعد الخروج من {self.JAIL_CUSTOM_TITLE}")
                    except discord.Forbidden:
                        print(f"[SystemBot] ⚠️ Cannot restore roles for {target.display_name} - hierarchy check failed")
                    except discord.HTTPException as e:
                        print(f"[SystemBot] ⚠️ HTTP error restoring roles for {target.display_name}: {e}")
                
                # SECOND: Remove jail role
                jail_role_id = cfg("jail_role_id", bd)
                if jail_role_id:
                    jail_role = guild.get_role(int(jail_role_id))
                    if jail_role and jail_role in target.roles:
                        try:
                            await target.remove_roles(jail_role, reason=f"إخراج من {self.JAIL_CUSTOM_TITLE}")
                        except discord.Forbidden:
                            print(f"[SystemBot] ⚠️ Cannot remove jail role from {target.display_name} - hierarchy check failed")
                        except discord.HTTPException as e:
                            print(f"[SystemBot] ⚠️ HTTP error removing jail role from {target.display_name}: {e}")
                
                # THIRD: Clear saved roles from backup
                clear_jailed_user_roles(target.id, bd)
                
                await _add_success_reaction()
                await _smart_log(guild, bd, "admin",
                    _embed(f"🔓 إخراج من {self.JAIL_CUSTOM_TITLE}", 
                        f"المنفذ: {author.mention}\nالهدف: {target.mention}", C.SUCCESS,
                        footer=f"System Bot  •  on_message  •  {_now_str()}"))

            elif matched_action == "userinfo":
                tgt = target or author
                roles = [r.mention for r in tgt.roles if not r.is_default()]
                e = _embed(f"🔍 {tgt.display_name}", "", C.INFO)
                e.add_field(name="الاسم", value=str(tgt), inline=True)
                e.add_field(name="ID", value=f"`{tgt.id}`", inline=True)
                e.add_field(name="انضم", value=tgt.joined_at.strftime("%Y-%m-%d") if tgt.joined_at else "—", inline=True)
                e.add_field(name="في روم", value=tgt.voice.channel.mention if tgt.voice else "لا", inline=True)
                e.add_field(name="الرتب", value=" ".join(roles[:8]) or "—", inline=False)
                e.set_thumbnail(url=tgt.display_avatar.url)
                await message.reply(embed=e)

            elif matched_action == "serverinfo":
                g = guild
                e = _embed(f"🏛️ {g.name}", "", C.GOLD)
                e.add_field(name="الأعضاء", value=f"{g.member_count:,}", inline=True)
                e.add_field(name="الرومات", value=f"{len(g.channels)}", inline=True)
                e.add_field(name="الأونر", value=g.owner.mention if g.owner else "—", inline=True)
                if g.icon: e.set_thumbnail(url=g.icon.url)
                await message.reply(embed=e)

            elif matched_action == "roleinfo":
                parts = matched_args.split()
                if not parts: return
                try:
                    role = guild.get_role(int(parts[0].strip("<@&>")))
                    if not role: return
                    count = sum(1 for m in guild.members if role in m.roles)
                    e = _embed(f"🎭 {role.name}", f"الأعضاء: **{count}** | الموقع: **{role.position}**", C.GOLD)
                    await message.reply(embed=e)
                except ValueError:
                    pass

            elif matched_action == "banlist":
                bans = [entry async for entry in guild.bans(limit=10)]
                lines = [f"`{b.user.id}` {b.user}" for b in bans]
                await message.reply(embed=_embed(
                    f"📋 المحظورون ({len(bans)}+)",
                    "\n".join(lines) or "لا يوجد محظورون.", C.DANGER))

            elif matched_action == "whois":
                tgt = target or author
                flags = []
                if tgt.bot: flags.append("🤖 بوت")
                if tgt.guild_permissions.administrator: flags.append("👑 مدير")
                e = _embed(f"🕵️ {tgt.display_name}",
                            " | ".join(flags) or "عضو عادي", C.PURPLE)
                e.add_field(name="ID", value=f"`{tgt.id}`", inline=True)
                e.add_field(name="في روم صوتي", value=tgt.voice.channel.name if tgt.voice else "لا", inline=True)
                e.set_thumbnail(url=tgt.display_avatar.url)
                await message.reply(embed=e)

            elif matched_action == "lockdown":
                if not author.guild_permissions.administrator:
                    return await _reply_err("هذا الأمر للمدير فقط.")
                reason = matched_args or "طوارئ"
                locked = 0
                for ch in guild.text_channels:
                    try:
                        await ch.set_permissions(guild.default_role, send_messages=False,
                                                 reason=f"LOCKDOWN — {reason}")
                        locked += 1
                    except: pass
                set_cfg("lockdown_active", True, bd)
                await _add_success_reaction()
                await _smart_log(guild, bd, "admin",
                    _embed("🚨 LOCKDOWN", f"المنفذ: {author.mention}\nالرومات: {locked}\nالسبب: {reason}",
                           C.DANGER, footer=f"System Bot  •  Lockdown  •  {_now_str()}"))

            elif matched_action == "unlockdown":
                if not author.guild_permissions.administrator:
                    return
                unlocked = 0
                for ch in guild.text_channels:
                    try:
                        await ch.set_permissions(guild.default_role, send_messages=True)
                        unlocked += 1
                    except: pass
                set_cfg("lockdown_active", False, bd)
                await _add_success_reaction()

            elif matched_action == "unban":
                parts = matched_args.split()
                if not parts: return
                try:
                    uid = int(parts[0])
                    obj = discord.Object(id=uid)
                    await guild.unban(obj)
                    await _add_success_reaction()
                except ValueError:
                    pass
                except discord.NotFound:
                    pass

            elif matched_action == "deafen":
                if not target: return
                await target.edit(deafen=True)
                await _add_success_reaction()

            elif matched_action == "undeafen":
                if not target: return
                await target.edit(deafen=False)
                await _add_success_reaction()

            elif matched_action == "pin":
                # pin MessageID
                parts = matched_args.split()
                if not parts: return await _reply_err("صيغة: `الاسم MessageID`")
                try:
                    msg_to_pin = await message.channel.fetch_message(int(parts[0]))
                    await msg_to_pin.pin()
                    await _reply_ok("الرسالة ثُبِّتت. 📌")
                except Exception as ex:
                    await _reply_err(f"خطأ: {ex}")

        except discord.Forbidden:
            pass  # Ignore permission errors
        except discord.HTTPException as ex:
            pass  # Ignore HTTP errors
        except Exception as ex:
            print(f"[SystemBot] on_message error [{matched_action}]: {ex}")
            pass  # Ignore unexpected errors


        ch_id = cfg("log_channel", self._bot_dir)
        if not ch_id:
            return None
        return guild.get_channel(int(ch_id))

    # ══════════════════════════════════════════════════════════════════════════
    # أمر الاقتباس (") — حذف رومات جماعي بـ ChannelSelect
    # ══════════════════════════════════════════════════════════════════════════
    async def _mass_delete_channels_cmd(self, message: discord.Message):
        """يُرسل واجهة ChannelSelect لاختيار رومات وحذفها دفعة واحدة"""
        bd = self._bot_dir
        if not _has_admin_permission(message.author, bd):
            return  # Silent denial - no response
            return
        view = MassDeleteChannelsView(self, message.author)
        try:
            await message.reply(
                embed=_embed(
                    "🗑️ حذف رومات جماعي",
                    "اختر الرومات التي تريد حذفها (يمكن اختيار أكثر من روم).\n"
                    "⚠️ سيُحذف كل روم مختار فوراً بدون تأكيد إضافي.",
                    C.DANGER),
                view=view)
        except Exception: pass

    async def on_message_delete(self, message: discord.Message):
        # Check if this was a pending sanction command
        if hasattr(self, '_pending_sanctions') and message.id in self._pending_sanctions:
            pending = self._pending_sanctions[message.id]
            try:
                # Revert the sanction
                await pending["revert_func"]()
                
                # Delete the menu message if still exists
                if "menu_msg" in pending and pending["menu_msg"]:
                    try:
                        await pending["menu_msg"].delete()
                    except Exception:
                        pass
                
                # Remove from tracking
                del self._pending_sanctions[message.id]
            except Exception:
                pass
        
        # Original logging logic
        if not message.guild or not self._guild_ok(message.guild.id):
            return
        if not bool(cfg("feature_log", self._bot_dir)):
            return
        if message.author.bot:
            return
        e = discord.Embed(title="🗑️  رسالة محذوفة", color=C.DANGER.value)
        e.add_field(name="المرسل",
                    value=f"{message.author.mention}\n`{message.author.id}`", inline=True)
        e.add_field(name="الروم", value=message.channel.mention, inline=True)
        e.add_field(name="المحتوى",
                    value=(message.content[:1000] if message.content else "*لا يوجد نص*"),
                    inline=False)
        if message.attachments:
            e.add_field(name="المرفقات",
                        value="\n".join(a.filename for a in message.attachments[:5]),
                        inline=False)
        e.set_footer(text=f"System Bot  •  Log  •  {_now_str()}")
        e.set_thumbnail(url=message.author.display_avatar.url)
        await _smart_log(message.guild, self._bot_dir, "chat", e)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle reaction room unlock system with proper member fetching and error handling"""
        if not self._guild_ok(payload.guild_id):
            return
        
        # Ignore bot's own reactions
        if payload.user_id == self.user.id:
            return
        
        bd = self._bot_dir
        guild = self.get_guild(payload.guild_id)
        if not guild:
            try:
                guild = await self.fetch_guild(payload.guild_id)
            except discord.NotFound:
                return
            except discord.HTTPException:
                return
        if not guild:
            return
        
        # Check if reaction room feature is enabled
        if not bool(cfg("feature_reaction_room", bd)):
            return
        
        # Handle NEW multi-room reaction system
        reaction_rooms_config = cfg("reaction_rooms_config", bd) or {}
        if reaction_rooms_config:
            # Check if this message is in any configured reaction room
            channel_id_str = str(payload.channel_id)
            if channel_id_str in reaction_rooms_config:
                room_config = reaction_rooms_config[channel_id_str]
                expected_emoji = room_config.get("emoji")
                member_role_ids = room_config.get("member_roles", [])
                writer_role_id = room_config.get("writer_role")
                
                if expected_emoji and member_role_ids:
                    try:
                        reaction_emoji = str(payload.emoji)
                        if reaction_emoji == expected_emoji:
                            # Safely fetch member
                            try:
                                member = guild.get_member(payload.user_id)
                                if not member:
                                    member = await guild.fetch_member(payload.user_id)
                            except discord.NotFound:
                                return
                            except discord.HTTPException:
                                return
                            
                            if member.bot:
                                return
                            
                            # Check if member has writer role (whitelisted)
                            writer_role = guild.get_role(writer_role_id) if writer_role_id else None
                            is_writer = writer_role and writer_role in member.roles
                            
                            # Grant member roles if not writer
                            if not is_writer:
                                async def _grant_roles():
                                    try:
                                        for role_id in member_role_ids:
                                            role = guild.get_role(role_id)
                                            if role and role not in member.roles:
                                                await member.add_roles(role, reason="Reaction Room unlock")
                                                print(f"[SystemBot] Granted role {role_id} to {member.name} for reaction room unlock")
                                                await asyncio.sleep(0.5)  # Rate limit delay
                                    except discord.Forbidden:
                                        print(f"[SystemBot] ⚠️ Cannot grant roles to {member.display_name} - hierarchy check failed")
                                    except discord.HTTPException as e:
                                        print(f"[SystemBot] ⚠️ HTTP error granting roles to {member.display_name}: {e}")
                                
                                asyncio.create_task(_grant_roles())
                            return
                    except Exception:
                        pass
        
        # Handle OLD single reaction room system (legacy support)
        rr_ch_id = cfg("reaction_room_channel", bd)
        rr_msg_id = cfg("reaction_room_message_id", bd)
        rr_emoji = cfg("reaction_room_emoji", bd)
        rr_member_role_id = cfg("reaction_room_member_role", bd)
        rr_writer_role_id = cfg("reaction_room_writer_role", bd)
        
        if not all([rr_ch_id, rr_msg_id, rr_emoji, rr_member_role_id]):
            return
        
        # Check if this is the tracked message and correct emoji
        if payload.message_id != int(rr_msg_id):
            return
        
        try:
            # Convert emoji string to actual emoji for comparison
            reaction_emoji = str(payload.emoji)
            if reaction_emoji != rr_emoji:
                return
        except Exception:
            return
        
        # Safely fetch member - don't rely on payload.member
        try:
            member = guild.get_member(payload.user_id)
            if not member:
                member = await guild.fetch_member(payload.user_id)
        except discord.NotFound:
            return
        except discord.HTTPException:
            return
        
        if member.bot:
            return
        
        backup_data = cfg("reaction_room_backup", bd) or {}
        member_role = guild.get_role(int(rr_member_role_id))
        writer_role = guild.get_role(int(rr_writer_role_id)) if rr_writer_role_id else None
        
        # Check if user has writer role (whitelisted - should not be locked)
        is_writer = writer_role and writer_role in member.roles
        
        if str(member.id) in backup_data:
            # Existing member - restore their original roles
            saved_role_ids = backup_data[str(member.id)]
            roles_to_restore = []
            for rid in saved_role_ids:
                role_obj = guild.get_role(rid)
                if role_obj and role_obj < guild.me.top_role:
                    roles_to_restore.append(role_obj)
            
            if roles_to_restore:
                async def _restore_roles():
                    try:
                        await member.add_roles(*roles_to_restore, reason="فتح السيرفر - نظام الرياكشن")
                        print(f"[DEBUG] Reaction Room: Restored roles for {member.name}: {[r.name for r in roles_to_restore]}")
                    except discord.Forbidden:
                        print(f"[SystemBot] ⚠️ Cannot restore roles for {member.display_name} - hierarchy check failed")
                    except discord.HTTPException as e:
                        print(f"[SystemBot] ⚠️ HTTP error restoring roles for {member.display_name}: {e}")
                    except Exception as e:
                        print(f"[SystemBot] Error restoring roles for {member.display_name}: {e}")
                asyncio.create_task(_restore_roles())
            
            # Remove from backup
            backup_data.pop(str(member.id), None)
            set_cfg("reaction_room_backup", backup_data, bd)
            
            # Check if all members have been restored
            if not backup_data:
                # Clear message ID tracking
                set_cfg("reaction_room_message_id", 0, bd)
        
        # Always assign member role if they don't have it (handles re-adding reaction)
        # Active Sanction Roles Verification - Prevent role conflicts
        mute_role_id = cfg("mute_role", bd)
        jail_role_id = cfg("jail_role_id", bd)
        
        # Check if member has active jail or mute role
        has_active_sanction = False
        if mute_role_id and any(r.id == int(mute_role_id) for r in member.roles):
            has_active_sanction = True
        if jail_role_id and any(r.id == int(jail_role_id) for r in member.roles):
            has_active_sanction = True
        
        if member_role and member_role not in member.roles and not has_active_sanction:
            async def _assign_member_role():
                try:
                    await member.add_roles(member_role, reason="عضو جديد - نظام الرياكشن")
                    print(f"[DEBUG] Reaction Room: Assigned member role to {member.name}")
                except discord.Forbidden:
                    print(f"[SystemBot] ⚠️ Cannot assign member role to {member.display_name} - hierarchy check failed")
                except discord.HTTPException as e:
                    print(f"[SystemBot] ⚠️ HTTP error assigning member role to {member.display_name}: {e}")
                except Exception as e:
                    print(f"[SystemBot] Error assigning member role to {member.display_name}: {e}")
            asyncio.create_task(_assign_member_role())

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Handle reaction removal for reaction room system with proper member fetching and error handling"""
        if not self._guild_ok(payload.guild_id):
            return
        
        # Ignore bot's own reactions
        if payload.user_id == self.user.id:
            return
        
        bd = self._bot_dir
        guild = self.get_guild(payload.guild_id)
        if not guild:
            try:
                guild = await self.fetch_guild(payload.guild_id)
            except discord.NotFound:
                return
            except discord.HTTPException:
                return
        if not guild:
            return
        
        # Check if reaction room feature is enabled
        if not bool(cfg("feature_reaction_room", bd)):
            return
        
        # Handle NEW multi-room reaction system
        reaction_rooms_config = cfg("reaction_rooms_config", bd) or {}
        if reaction_rooms_config:
            # Check if this message is in any configured reaction room
            channel_id_str = str(payload.channel_id)
            if channel_id_str in reaction_rooms_config:
                room_config = reaction_rooms_config[channel_id_str]
                expected_emoji = room_config.get("emoji")
                member_role_ids = room_config.get("member_roles", [])
                writer_role_id = room_config.get("writer_role")
                
                if expected_emoji and member_role_ids:
                    try:
                        reaction_emoji = str(payload.emoji)
                        if reaction_emoji == expected_emoji:
                            # Safely fetch member
                            try:
                                member = guild.get_member(payload.user_id)
                                if not member:
                                    member = await guild.fetch_member(payload.user_id)
                            except discord.NotFound:
                                return
                            except discord.HTTPException:
                                return
                            
                            if member.bot:
                                return
                            
                            # Check if member has writer role (whitelisted)
                            writer_role = guild.get_role(writer_role_id) if writer_role_id else None
                            is_writer = writer_role and writer_role in member.roles
                            
                            # Revoke member roles if not writer
                            if not is_writer:
                                async def _revoke_roles():
                                    try:
                                        for role_id in member_role_ids:
                                            role = guild.get_role(role_id)
                                            if role and role in member.roles:
                                                await member.remove_roles(role, reason="Reaction Room reaction removed")
                                                print(f"[SystemBot] Revoked role {role_id} from {member.name} for reaction room lock")
                                                await asyncio.sleep(0.5)  # Rate limit delay
                                    except discord.Forbidden:
                                        print(f"[SystemBot] ⚠️ Cannot revoke roles from {member.display_name} - hierarchy check failed")
                                    except discord.HTTPException as e:
                                        print(f"[SystemBot] ⚠️ HTTP error revoking roles from {member.display_name}: {e}")
                                
                                asyncio.create_task(_revoke_roles())
                            return
                    except Exception:
                        pass
        
        # Handle OLD single reaction room system (legacy support)
        rr_ch_id = cfg("reaction_room_channel", bd)
        rr_msg_id = cfg("reaction_room_message_id", bd)
        rr_emoji = cfg("reaction_room_emoji", bd)
        rr_member_role_id = cfg("reaction_room_member_role", bd)
        rr_writer_role_id = cfg("reaction_room_writer_role", bd)
        
        if not all([rr_ch_id, rr_msg_id, rr_emoji, rr_member_role_id]):
            return
        
        # Check if this is the tracked message and correct emoji
        if payload.message_id != int(rr_msg_id):
            return
        
        try:
            # Convert emoji string to actual emoji for comparison
            reaction_emoji = str(payload.emoji)
            if reaction_emoji != rr_emoji:
                return
        except Exception:
            return
        
        # Safely fetch member - don't rely on payload.member (unavailable in remove events)
        try:
            member = guild.get_member(payload.user_id)
            if not member:
                member = await guild.fetch_member(payload.user_id)
        except discord.NotFound:
            return
        except discord.HTTPException:
            return
        
        if member.bot:
            return
        
        backup_data = cfg("reaction_room_backup", bd) or {}
        member_role = guild.get_role(int(rr_member_role_id))
        writer_role = guild.get_role(int(rr_writer_role_id)) if rr_writer_role_id else None
        
        # Check if user has writer role (whitelisted - should not be locked)
        is_writer = writer_role and writer_role in member.roles
        
        # Remove member role if they have it
        if member_role and member_role in member.roles:
            async def _remove_member_role():
                try:
                    await member.remove_roles(member_role, reason="إزالة رياكشن - إعادة قفل")
                    print(f"[DEBUG] Reaction Room: Removed member role from {member.name}")
                except discord.Forbidden:
                    print(f"[SystemBot] ⚠️ Cannot remove member role from {member.display_name} - hierarchy check failed")
                except discord.HTTPException as e:
                    print(f"[SystemBot] ⚠️ HTTP error removing member role from {member.display_name}: {e}")
            asyncio.create_task(_remove_member_role())
        
        # Only strip roles if user is NOT whitelisted (doesn't have writer role)
        if not is_writer:
            # Backup their current roles before stripping
            current_role_ids = [r.id for r in member.roles if not r.is_default() and not r.managed]
            bot_top_role = guild.me.top_role if guild.me else None
            roles_to_remove = []
            for r in member.roles:
                if r.is_default() or r.managed:
                    continue
                if bot_top_role and r.position >= bot_top_role.position:
                    continue
                roles_to_remove.append(r)
            
            if roles_to_remove:
                async def _strip_roles():
                    try:
                        await member.remove_roles(*roles_to_remove, reason="إزالة رياكشن - إعادة قفل")
                        print(f"[DEBUG] Reaction Room: Stripped roles from {member.name}: {[r.name for r in roles_to_remove]}")
                    except discord.Forbidden:
                        print(f"[SystemBot] ⚠️ Cannot remove roles for {member.display_name} - hierarchy check failed")
                    except discord.HTTPException as e:
                        print(f"[SystemBot] ⚠️ HTTP error removing roles for {member.display_name}: {e}")
                asyncio.create_task(_strip_roles())
            
            # Add them to backup for restoration when they re-add reaction
            backup_data[str(member.id)] = current_role_ids
            set_cfg("reaction_room_backup", backup_data, bd)
            
            print(f"[DEBUG] Reaction Room: Re-locked {member.name} after reaction removal (not whitelisted)")
        else:
            print(f"[DEBUG] Reaction Room: Skipped locking {member.name} (has writer role - whitelisted)")

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not after.guild or not self._guild_ok(after.guild.id):
            return
        if not bool(cfg("feature_log", self._bot_dir)):
            return
        if after.author.bot or before.content == after.content:
            return
        e = discord.Embed(title="✏️  رسالة معدَّلة", color=C.WARNING.value)
        e.add_field(name="المرسل",
                    value=f"{after.author.mention}\n`{after.author.id}`", inline=True)
        e.add_field(name="الروم", value=after.channel.mention, inline=True)
        e.add_field(name="قبل", value=(before.content[:500] or "*فارغ*"), inline=False)
        e.add_field(name="بعد", value=(after.content[:500]  or "*فارغ*"), inline=False)
        e.add_field(name="الرابط", value=f"[اضغط هنا]({after.jump_url})", inline=True)
        e.set_footer(text=f"System Bot  •  Log  •  {_now_str()}")
        e.set_thumbnail(url=after.author.display_avatar.url)
        await _smart_log(after.guild, self._bot_dir, "chat", e)

    async def on_member_remove(self, member: discord.Member):
        if not self._guild_ok(member.guild.id):
            return
        if not bool(cfg("feature_log", self._bot_dir)):
            return

        # ── تحقق من audit log: هل الخروج بسبب طرد؟ ──────────────────────
        await asyncio.sleep(1)
        kicked_by = None
        kick_reason = None
        try:
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    kicked_by  = entry.user
                    kick_reason = entry.reason
                    break
        except Exception:
            pass

        if kicked_by:
            # ── لوق طرد (بدل لوق خروج) ───────────────────────────────────
            log_content = f"""-------------------------------
# لوق طرد
العضو: {member.mention}
المنفذ: {kicked_by.mention}
السبب: {kick_reason or '—'}
-------------------------------"""
            await _smart_log(member.guild, self._bot_dir, "admin", log_content)
        else:
            # ── خروج طبيعي ───────────────────────────────────────────────
            date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            log_content = f"""-------------------------------
# لوق خروج
العضو: {member.mention}
المعرف: {member.id}
التاريخ: {date_str}
-------------------------------"""
            await _smart_log(member.guild, self._bot_dir, "join_leave", log_content)

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Detect manual mute/jail role removal and restore saved roles"""
        if not self._guild_ok(after.guild.id):
            return
        
        bd = self._bot_dir
        guild = after.guild
        
        # Check if mute role was removed - ONLY use muted_users_roles key
        mute_role_id = cfg("mute_role", bd)
        if mute_role_id:
            mute_role = guild.get_role(int(mute_role_id))
            if mute_role:
                had_mute_before = mute_role in before.roles
                has_mute_after = mute_role in after.roles
                if had_mute_before and not has_mute_after:
                    # Mute role was manually removed - restore roles from muted_users_roles ONLY
                    saved_role_ids = load_muted_user_roles(after.id, bd)
                    if saved_role_ids:
                        roles_to_restore = []
                        for rid in saved_role_ids:
                            role_obj = guild.get_role(rid)
                            if role_obj and role_obj < guild.me.top_role:  # ensure bot has hierarchy permission
                                roles_to_restore.append(role_obj)
                        
                        if roles_to_restore:
                            try:
                                print(f"[DEBUG] on_member_update mute: Restoring roles for {after.name}: {[r.name for r in roles_to_restore]}")
                                await after.add_roles(*roles_to_restore, reason="استعادة الرتب بعد إزالة الكتم يدوياً")
                                clear_muted_user_roles(after.id, bd)
                                print(f"[SystemBot] ✅ Restored roles for {after.display_name} after manual unmute")
                            except Exception:
                                pass
        
        # Check if jail role was removed - ONLY use jailed_users_roles key
        jail_role_id = cfg("jail_role_id", bd)
        if jail_role_id:
            jail_role = guild.get_role(int(jail_role_id))
            if jail_role:
                had_jail_before = jail_role in before.roles
                has_jail_after = jail_role in after.roles
                if had_jail_before and not has_jail_after:
                    # Jail role was manually removed - restore roles from jailed_users_roles ONLY
                    saved_role_ids = load_jailed_user_roles(after.id, bd)
                    if saved_role_ids:
                        roles_to_restore = []
                        for rid in saved_role_ids:
                            role_obj = guild.get_role(rid)
                            if role_obj and role_obj < guild.me.top_role:  # ensure bot has hierarchy permission
                                roles_to_restore.append(role_obj)
                        
                        if roles_to_restore:
                            try:
                                print(f"[DEBUG] on_member_update jail: Restoring roles for {after.name}: {[r.name for r in roles_to_restore]}")
                                await after.add_roles(*roles_to_restore, reason=f"استعادة الرتب بعد إزالة {self.JAIL_CUSTOM_TITLE} يدوياً")
                                clear_jailed_user_roles(after.id, bd)
                                print(f"[SystemBot] ✅ Restored roles for {after.display_name} after manual unjail")
                            except Exception:
                                pass

    async def on_error(self, event, *args, **kwargs):
        traceback.print_exc()

    # ── تسجيل الأوامر ─────────────────────────────────────────────────────────
    async def _register_commands(self):
        tree = self.tree
        bot  = self

        # ── /settings ────────────────────────────────────────────────────────
        @tree.command(name="settings", description="أرسل لوحة الإعداد في الروم الحالية")
        async def settings_cmd(interaction: discord.Interaction):
            # Check Bot Manager permission using dynamic permission function
            if not _has_bot_manager_permission(interaction.user, bot._bot_dir):
                return  # Silent denial - no response
            
            # No defer needed - send hub panel as direct response
            set_cfg("setup_channel", interaction.channel.id, bot._bot_dir)
            reload_config_for(bot)
            await interaction.response.send_message(
                content=f"**🤖 System Bot Premium**\n{interaction.user.mention} مرحباً بك في لوحة التحكم\n\nاضغط **بدء 🚀** لبدء إعداد البوت خطوة بخطوة.", 
                view=HubView(bot, interaction.user.id)
            )


# ══════════════════════════════════════════════════════════════════════════════
# دالة الإنشاء
# ══════════════════════════════════════════════════════════════════════════════
def create_system_bot(client_id: int, owner_discord_id: int,
                      bot_dir: str = None, allowed_guild_id: int = 0) -> SystemBot:
    return SystemBot(
        client_id=client_id,
        owner_discord_id=owner_discord_id,
        bot_dir=bot_dir,
        allowed_guild_id=allowed_guild_id,
    )


async def stop_bot_instance(bot: SystemBot):
    try:
        for guild in bot.guilds:
            if guild.owner_id == bot._owner_discord_id:
                setup_ch = guild.get_channel(bot.SETUP_CH)
                if setup_ch:
                    try:
                        await setup_ch.send(embed=_embed(
                            "🔴 البوت أُوقف",
                            "انتهى اشتراك البوت. للتجديد تواصل مع المتجر.",
                            C.DANGER))
                    except Exception:
                        pass
                break
        await bot.close()
    except Exception as ex:
        print(f"[SystemBot] ⚠️ خطأ إغلاق: {ex}")
