#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ArduinoJson.h>

// Pin utilise lors du branchement de l'ESP32-C3
#define SS_PIN 4
#define RST_PIN 3
MFRC522 mfrc522(SS_PIN, RST_PIN);

const char* ssid = "Bbox-CCC4FEF1";  // Ajouter votre Wifi ; attention 2.4GHz 
const char* password = "Lsxnx4DM!qA=KNYV";  // Ajouter votre code wifi
const char* base_url = "https://api-refid.onrender.com";  // URL de l'API
const char* admin_pin = "1234";  // Code PIN à valider pour admin


// Lecture identifiant du badge
String getUID() {
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

// Initialisation du Wifi - SPI - RFID
void setup() {
  Serial.begin(115200);
  delay(1000);

  WiFi.begin(ssid, password);
  Serial.print("Connexion WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnecté au WiFi !");
  Serial.print("Adresse IP ESP32 : ");
  Serial.println(WiFi.localIP());

  SPI.begin();
  mfrc522.PCD_Init();
  Serial.println("Lecteur RFID initialisé");
}

// Boucle principal
void loop() {

  // Attente de badge
  Serial.println("Attente badge...");
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    delay(1000);
    return;
  }

  // Si un badge scanné → récuperation identifiant
  String uid = getUID();
  Serial.print("UID détecté : ");
  Serial.println(uid);

  // 
  if ((WiFi.status() == WL_CONNECTED)) {
    HTTPClient http;
    http.begin(String(base_url) + "/check_badge");
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<200> doc;
    doc["uid"] = uid;
    String requestBody;
    serializeJson(doc, requestBody);

    int httpResponseCode = http.POST(requestBody);
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Réponse : " + response);

      StaticJsonDocument<200> res;
      deserializeJson(res, response);

      bool access = res["access"];

      if (!access) {
        Serial.println("Accès refusé ! UID inconnu.");
        return; // Stop ici si badge inconnu
      }

      const char* role = res["role"];
      const char* name = res["name"];
      
      // Si admin detecte → rentre code PIN
      if (String(role) == "admin") {
        Serial.println("Admin détecté. Entrez le code PIN :");
        while (!Serial.available());
        String pin = Serial.readStringUntil('\n');
        pin.trim();
        
        // Donne accès si authentifié 
        if (pin == admin_pin) {
          Serial.println("Authentifié ! Tapez 1 pour ajouter ou 2 pour supprimer un badge.");
          while (!Serial.available());
          char option = Serial.read();

          if (option == '1') {
            Serial.println("Scanner le badge à enregistrer");
            while (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial());
            String new_uid = getUID();
            Serial.print("UID : "); Serial.println(new_uid);

            Serial.println("Nom de l'utilisateur : ");
            while (!Serial.available());
            String new_name = Serial.readStringUntil('\n'); new_name.trim();

            Serial.println("Rôle ('admin' ou 'user') : ");
            while (!Serial.available());
            String new_role = Serial.readStringUntil('\n'); new_role.trim();

            // API ajoute un user
            HTTPClient addHttp;
            addHttp.begin(String(base_url) + "/add_user");
            addHttp.addHeader("Content-Type", "application/json");
            StaticJsonDocument<200> addDoc;
            addDoc["name"] = new_name;
            addDoc["role"] = new_role;
            addDoc["uid"] = new_uid;
            String jsonAdd;
            serializeJson(addDoc, jsonAdd);
            int r = addHttp.POST(jsonAdd);
            Serial.println(r > 0 ? "✅ Badge ajouté." : "❌ Échec ajout badge.");
            addHttp.end();

          } else if (option == '2') {  // Supprime un badge
            Serial.println("Scanner le badge à supprimer...");
            while (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial());
            String del_uid = getUID();

            HTTPClient delHttp;
            delHttp.begin(String(base_url) + "/delete_user");
            delHttp.addHeader("Content-Type", "application/json");
            StaticJsonDocument<100> delDoc;
            delDoc["uid"] = del_uid;
            String jsonDel;
            serializeJson(delDoc, jsonDel);
            int d = delHttp.POST(jsonDel);
            Serial.println(d > 0 ? "Badge supprimé." : "Échec suppression.");
            delHttp.end();
          } else {
            Serial.println("Option invalide");
          }
        } else {
          Serial.println("Code PIN incorrect");
        }
      } else {
        Serial.print("Bonjour ");  // Permet le passage
        Serial.println(name);
      }
    } else { 
      Serial.print("Erreur HTTP : ");   // Retourne l'erreur 
      Serial.println(httpResponseCode);
    }
    http.end();
  }
  delay(1500);
}
