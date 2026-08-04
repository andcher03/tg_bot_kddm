from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.residence.volunteer import volunteer_menu

router = Router()


@router.callback_query(F.data == "residence_volunteer")
async def volunteer(callback: CallbackQuery):

    await callback.message.edit_text(
        "🤝 <b>Волонтерство</b>\n\n"

        "Волонтерство — это возможность приобрести новый опыт, "
        "стать частью масштабных городских и республиканских событий, "
        "найти единомышленников и внести вклад в развитие общества.\n\n"

        "В этом разделе вы можете:\n"
        "• узнать о волонтерских организациях;\n"
        "• присоединиться к движению «Добро.рф»;\n"
        "• перейти в официальные сообщества;\n"
        "• связаться с координаторами.\n\n"

        "👇 Выберите интересующий пункт:",

        reply_markup=volunteer_menu()
    )

    await callback.answer()