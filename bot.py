import logging
from datetime import datetime
from telegram import Update, Poll
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import gspread # type: ignore

# Configurar el logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Variables del bot y Google Sheets
TOKEN_BOT = '7695366938:AAFdpSLDXMom1fgXg3UGWnuX-h4w958MpXI'
SHEET_ID = '1meJnfziPVE_WeS4fXA_Af434ttWmCI7uCWhjFIRv7Kc'

# Conectar con Google Sheets
gc = gspread.service_account(filename='credentials.json')
spreadsheet = gc.open_by_key(SHEET_ID)
hoja = spreadsheet.worksheet('CalendarioLEC25')

async def calendario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    hoy = datetime.now().strftime('%d/%m/%Y')
    partidos = hoja.get_all_values()
    mensaje = f'Partidos para hoy ({hoy}):\n\n'
    for fila in partidos[1:]:
        if fila[0] == hoy:
            for i in range(3, len(fila)):
                if 'vs' in fila[i]:
                    mensaje += f'{fila[0]}: {fila[i]}\n'
    if mensaje == f'Partidos para hoy ({hoy}):\n\n':
        mensaje = 'No hay partidos programados para hoy.'
    await update.message.reply_text(mensaje)

async def encuesta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    hoy = datetime.now().strftime('%d/%m/%Y')
    partidos = hoja.get_all_values()
    for fila in partidos[1:]:
        if fila[0] == hoy:
            tipo_partido = fila[2]
            for i in range(3, len(fila)):
                if 'vs' in fila[i]:
                    equipos = fila[i].split(' vs ')
                    equipo1 = equipos[0]
                    equipo2 = equipos[1]
                    if tipo_partido == 'Bo1':
                        opciones = [equipo1, equipo2]
                    elif tipo_partido == 'Bo3':
                        opciones = [f'{equipo1} 2-0 {equipo2}', f'{equipo1} 2-1 {equipo2}', f'{equipo1} 1-2 {equipo2}', f'{equipo1} 0-2 {equipo2}']
                    elif tipo_partido == 'Bo5':
                        opciones = [f'{equipo1} 3-0 {equipo2}', f'{equipo1} 3-1 {equipo2}', f'{equipo1} 3-2 {equipo2}', f'{equipo1} 2-3 {equipo2}', f'{equipo1} 1-3 {equipo2}', f'{equipo1} 0-3 {equipo2}']
                    else:
                        continue
                    await update.message.reply_poll(
                        question=f'¿Quién ganará? {equipo1} vs {equipo2}',
                        options=opciones,
                        is_anonymous=False
                    )

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN_BOT).build()

    application.add_handler(CommandHandler('calendario', calendario))
    application.add_handler(CommandHandler('encuesta', encuesta))

    application.run_polling()
