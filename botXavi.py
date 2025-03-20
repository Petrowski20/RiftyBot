import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler, ApplicationBuilder, ContextTypes
import gspread # type: ignore

# Configurar el logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

import os

# Conectar con Google Sheets
import json
import base64

creds_json = base64.b64decode(os.getenv("GOOGLE_CREDENTIALS")).decode("utf-8")
creds_dict = json.loads(creds_json)

gc = gspread.service_account_from_dict(creds_dict)
spreadsheet = gc.open_by_key(SHEET_ID)
hoja = spreadsheet.worksheet('CalendarioLEC25')

def obtener_partidos_hoy():
    hoy = datetime.now().strftime('%d/%m/%Y')
    partidos = hoja.get_all_values()
    partidos_hoy = [fila for fila in partidos[1:] if fila[0] == hoy]
    return hoy, partidos_hoy

async def calendario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    hoy, partidos_hoy = obtener_partidos_hoy()
    mensaje = f'Partidos para hoy ({hoy}):\n\n'
    for fila in partidos_hoy:
        for i in range(3, len(fila)):
            if 'vs' in fila[i]:
                mensaje += f'{fila[0]}: {fila[i]}\n'
    if mensaje == f'Partidos para hoy ({hoy}):\n\n':
        mensaje = 'No hay partidos programados para hoy.'
    await update.message.reply_text(mensaje)

async def encuesta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    hoy, partidos_hoy = obtener_partidos_hoy()
    for fila in partidos_hoy:
        tipo_partido = fila[2]
        for i in range(3, len(fila)):
            if 'vs' in fila[i]:
                equipo1, equipo2 = fila[i].split(' vs ')
                opciones = generar_opciones(tipo_partido, equipo1, equipo2)
                if opciones:
                    await update.message.reply_poll(
                        question=f'¿Quién ganará? {equipo1} vs {equipo2}',
                        options=opciones,
                        is_anonymous=False,
                        allows_multiple_answers=False
                    )


def generar_opciones(tipo_partido, equipo1, equipo2):
    if tipo_partido == 'Bo1':
        return [equipo1, equipo2]
    elif tipo_partido == 'Bo3':
        return [
            f'{equipo1} 2-0 {equipo2}', f'{equipo1} 2-1 {equipo2}', 
            f'{equipo1} 1-2 {equipo2}', f'{equipo1} 0-2 {equipo2}'
        ]
    elif tipo_partido == 'Bo5':
        return [
            f'{equipo1} 3-0 {equipo2}', f'{equipo1} 3-1 {equipo2}', f'{equipo1} 3-2 {equipo2}', 
            f'{equipo1} 2-3 {equipo2}', f'{equipo1} 1-3 {equipo2}', f'{equipo1} 0-3 {equipo2}'
        ]
    else:
        return None
async def guardar_respuesta_encuesta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    respuesta = update.poll_answer
    poll_id = respuesta.poll_id
    user_id = respuesta.user.id
    user_name = respuesta.user.first_name
    opcion_elegida = respuesta.option_ids[0]
    datos_encuesta = context.chat_data.get(poll_id)

    if datos_encuesta:
        partido = datos_encuesta['partido']
        hoja_resultados = spreadsheet.worksheet(datos_encuesta['InviernoLEC25'])
        valores = hoja_resultados.get_all_values()

        # Encontrar la columna del partido
        encabezados = valores[4]
        columna_partido = encabezados.index(partido)

        # Encontrar la fila del usuario
        nombres_usuarios = [fila[0] for fila in valores[5:]]
        fila_usuario = nombres_usuarios.index(user_name) + 6

        # Registrar el voto en la celda correcta
        hoja_resultados.update_cell(fila_usuario, columna_partido + 1, respuesta.options[opcion_elegida])

ligas_disponibles = ['LEC', 'LTA', 'LCK', 'Superliga']

# Almacenamiento temporal de selecciones de usuarios
registro_temporal = {}

async def participo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton(liga, callback_data=f'liga_{liga}')] for liga in ligas_disponibles]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Selecciona la liga en la que quieres participar:', reply_markup=reply_markup)

async def seleccionar_liga(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    liga_seleccionada = query.data.replace('liga_', '')
    registro_temporal[query.from_user.id] = {'liga': liga_seleccionada}
    
    await query.edit_message_text(text=f'Has seleccionado la liga: {liga_seleccionada}\nEscribe tu nombre para registrar tu participación.')

async def registrar_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    usuario_id = update.effective_user.id
    nombre_usuario = ' '.join(context.args)
    
    if usuario_id in registro_temporal:
        registro_temporal[usuario_id]['nombre'] = nombre_usuario
        liga = registro_temporal[usuario_id]['liga']
        
        # Aquí puedes guardar la información en la hoja de Google Sheets o en un array
        await update.message.reply_text(f'Te has registrado en {liga} con el nombre {nombre_usuario}.')
    else:
        await update.message.reply_text('Primero debes seleccionar una liga con /participo.')

    
async def pito(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Stefania guarra puerca')
async def botdemierda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('¡Eh! Respeta bro, respeta')
async def maricon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Marica el último, como mandan los cánones')

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN_BOT).build()
    application.add_handler(CommandHandler('calendario', calendario))
    application.add_handler(CommandHandler('encuesta', encuesta))
    application.add_handler(CommandHandler('participo', participo))
    application.add_handler(CallbackQueryHandler(seleccionar_liga, pattern='^liga_'))
    application.add_handler(CommandHandler('registrar', registrar_nombre))

    application.add_handler(CommandHandler('pito', pito))
    application.add_handler(CommandHandler('botdemierda', botdemierda))
    application.add_handler(CommandHandler('maricon', maricon))


    application.run_polling()
