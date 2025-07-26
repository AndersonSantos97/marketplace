import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List
from sqlmodel import select
from fastapi import HTTPException
import os


# Configuración de email (agregar a tu archivo de configuración)
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)

def send_sale_notification_email(seller_email: str, seller_name: str, sale_details: Dict):
    """
    Envía un correo de notificación de venta al vendedor
    """
    
    try:
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = seller_email
        msg['Subject'] = f"¡Nueva venta realizada! - Pedido #{sale_details['order_id']}"
        
        # Crear el cuerpo del email
        body = f"""
        <html>
        <body>
            <h2>¡Felicitaciones {seller_name}!</h2>
            <p>Se ha realizado una nueva venta de tu producto.</p>
            
            <h3>Detalles de la venta:</h3>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td><strong>Número de pedido:</strong></td>
                    <td>#{sale_details['order_id']}</td>
                </tr>
                <tr>
                    <td><strong>Fecha de venta:</strong></td>
                    <td>{sale_details['sale_date']}</td>
                </tr>
                <tr>
                    <td><strong>Comprador:</strong></td>
                    <td>{sale_details['buyer_name']} ({sale_details['buyer_email']})</td>
                </tr>
                <tr>
                    <td><strong>Total de la venta:</strong></td>
                    <td>${sale_details['total_amount']:.2f}</td>
                </tr>
                <tr>
                    <td><strong>Método de pago:</strong></td>
                    <td>{sale_details['payment_method']}</td>
                </tr>
            </table>
            
            <h3>Productos vendidos:</h3>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr>
                    <th>Producto</th>
                    <th>Cantidad</th>
                    <th>Precio unitario</th>
                    <th>Subtotal</th>
                </tr>
        """
        
        for item in sale_details['items']:
            body += f"""
                <tr>
                    <td>{item['product_title']}</td>
                    <td>{item['quantity']}</td>
                    <td>${item['price']:.2f}</td>
                    <td>${item['quantity'] * item['price']:.2f}</td>
                </tr>
            """
        
        body += """
            </table>
            
            <br>
            <p>Gracias por usar nuestra plataforma.</p>
            <p>Saludos cordiales,<br>El equipo de la plataforma</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Enviar el email
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, seller_email, text)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Error enviando email: {str(e)}")
        return False