# app/services/voucher_processor.py
import base64
import json
import os
from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import crud_yape_plin_transaction
from app.models.yape_plin_transaction import ExtractionStatus

from app.db.session import SessionLocal

client = OpenAI(api_key=settings.OPENAI_API_KEY)


# --- VERIFICACIÓN DE LA API KEY ---
api_key = settings.OPENAI_API_KEY
if not api_key or not api_key.startswith("sk-"):
    print("!!!!!!!!!! ALERTA: OPENAI_API_KEY no encontrada o con formato inválido. !!!!!!!!!!!")
    # Podríamos incluso lanzar un error aquí para detener la aplicación si la clave es vital
    # raise ValueError("OPENAI_API_KEY no configurada correctamente en el archivo .env")
else:
    print("--- INFO: OPENAI_API_KEY cargada correctamente. ---")

# Inicializamos el cliente de OpenAI
try:
    client = OpenAI(api_key=api_key)
    print("--- INFO: Cliente de OpenAI inicializado con éxito. ---")
except Exception as e:
    print(f"!!!!!!!!!! ERROR al inicializar el cliente de OpenAI: {e} !!!!!!!!!!!")
    client = None
# -----------------------------------


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_voucher_image(transaction_id: int, image_path: str):
    if not client:
        print(f"[{transaction_id}] Abortando: El cliente de OpenAI no está inicializado.")
        # Marcar la transacción como fallida
        # ...
        return
    # ... resto de la lógica de la función

    print(f"[{transaction_id}] Iniciando procesamiento IA para el voucher: {image_path}")

     # --- CREAR UNA NUEVA SESIÓN DE DB ---
    db = SessionLocal()
    # ------------------------------------

    try:
        base64_image = encode_image_to_base64(image_path)

        prompt_messages = [
            {
                "role": "system",
                "content": """
                Eres un asistente contable experto en Perú, especializado en analizar vouchers de pago de Yape y Plin.
                Tu tarea es extraer información clave de la imagen de un voucher.
                Responde ÚNICAMENTE con un objeto JSON. No incluyas texto explicativo, ni la palabra "json" al principio.
                El JSON debe tener la siguiente estructura:
                {
                  "monto": float,
                  "moneda": "PEN",
                  "numero_operacion": "string",
                  "nombre_destinatario": "string",
                  "nombre_remitente": "string",
                  "fecha": "string en formato YYYY-MM-DD",
                  "hora": "string en formato HH:MM:SS"
                }
                Si algún campo no se puede extraer, déjalo como null.
                """
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extrae los datos de este voucher."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=prompt_messages,
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        extracted_data_str = response.choices[0].message.content
        extracted_data = json.loads(extracted_data_str)
        
        print(f"[{transaction_id}] Datos extraídos por IA: {extracted_data}")

        crud_yape_plin_transaction.update_transaction_from_ai(
            db=db,
            transaction_id=transaction_id,
            ai_data=extracted_data,
            new_status=ExtractionStatus.LLM_EXTRACTION_COMPLETED
        )
        print(f"[{transaction_id}] Base de datos actualizada con éxito.")
    except Exception as e:
        print(f"!!! ERROR en el procesamiento IA para la transacción {transaction_id}: {e}")
        crud_yape_plin_transaction.update_transaction_status(
            db=db,
            transaction_id=transaction_id,
            new_status=ExtractionStatus.LLM_FAILED,
            notes=str(e)
        )
    finally:
        # Limpieza: Elimina el archivo de imagen temporal después de procesarlo
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"[{transaction_id}] Archivo temporal eliminado: {image_path}")