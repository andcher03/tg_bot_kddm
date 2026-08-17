from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def university_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏛 КФУ", callback_data="uni_kfu")],
            [InlineKeyboardButton(text="✈️ КНИТУ-КАИ", callback_data="uni_kai")],
            [InlineKeyboardButton(text="🧪 КНИТУ", callback_data="uni_khti")],
            [InlineKeyboardButton(text="⚡ КГЭУ", callback_data="uni_kgeu")],
            [InlineKeyboardButton(text="🏗 КГАСУ", callback_data="uni_kgasu")],
            [InlineKeyboardButton(text="⚕️ КазГМУ", callback_data="uni_kgmu")],
            [InlineKeyboardButton(text="🎓 Университет управления ТИСБИ", callback_data="uni_tisbi")],
            [InlineKeyboardButton(text="📚 Другой ВУЗ", callback_data="uni_other")],
        ]
    )