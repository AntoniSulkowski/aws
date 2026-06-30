import json
import urllib.request
import boto3
import datetime
import uuid

S3_RAW_BUCKET = "weather-raw-data-198093-197564"
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:738016995889:WeatherAlerts"
DYNAMODB_TABLE = "WeatherAlertHistory"
API_URL = "https://e6uw49pbah.execute-api.us-east-1.amazonaws.com/dev/weather/latest?station_id=GDN_01"

s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    timestamp_now = datetime.datetime.now().isoformat()
    
    req = urllib.request.Request(API_URL)
    req.add_header('Authorization', 'Bearer STUDENT_TOKEN_2026')
    
    try:
        with urllib.request.urlopen(req) as response:
            raw_response = response.read().decode('utf-8')
            weather_data = json.loads(raw_response)
    except Exception as e:
        print(f"Błąd API: {e}")
        return {"statusCode": 500, "body": "Błąd API"}

    file_name = f"raw_data/gdn_01_{timestamp_now}.json"
    s3.put_object(
        Bucket=S3_RAW_BUCKET, 
        Key=file_name, 
        Body=json.dumps(weather_data)
    )
    print(f"Zapisano dane surowe do S3: {file_name}")

    alerts_triggered = []
    
    wind_speed = weather_data.get('wind_speed', 0)
    temperature = weather_data.get('temperature', 0)
    rain_mm = weather_data.get('rain_mm', 0)

    if wind_speed > 15.0:
        alerts_triggered.append(f"Silny wiatr: {wind_speed} m/s")
    if temperature < 2.0 and rain_mm > 0:
        alerts_triggered.append(f"Ryzyko gołoledzi! Temp: {temperature}C, Opad: {rain_mm}mm")
    if temperature > 35.0:
        alerts_triggered.append(f"Ekstremalny upał: {temperature}C")

    if alerts_triggered:
        alert_message = " | ".join(alerts_triggered)
        station = weather_data.get('station_id', 'GDN_01')
        
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(Item={
            'alert_id': str(uuid.uuid4()),
            'timestamp': timestamp_now,
            'station_id': station,
            'triggered_rules': alert_message,
            'current_temp': str(temperature),
            'current_wind': str(wind_speed)
        })
        print("Zapisano alert do DynamoDB.")

        email_body = (
            f"OSTRZEŻENIE POGODOWE DLA STACJI {station}\n"
            f"Czas: {timestamp_now}\n\n"
            f"Wykryte zagrożenia:\n- {chr(10) + '- '.join(alerts_triggered)}\n\n"
            f"Dane JSON:\n{json.dumps(weather_data, indent=2)}"
        )
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=email_body,
            Subject=f"Alert Pogodowy - {station}"
        )
        print("Wysłano e-mail.")
    else:
        print("Parametry w normie, brak alertów.")

    return {
        "statusCode": 200,
        "body": json.dumps({"status": "sukces", "alerts": alerts_triggered})
    }