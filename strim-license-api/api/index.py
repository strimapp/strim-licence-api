# File: api/index.py
import os
import json
import datetime
from http.server import BaseHTTPRequestHandler
from supabase import create_client, Client

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Baca data JSON dari request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        key_to_check = data.get('license_key')

        if not key_to_check:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"valid": False, "message": "Kunci lisensi tidak disediakan."}).encode())
            return
        
        try:
            # Inisialisasi koneksi ke Supabase
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY")
            supabase: Client = create_client(supabase_url, supabase_key)

            # Cari kunci di tabel 'licenses'
            response = supabase.table('licenses').select('*').eq('license_key', key_to_check).execute()
            
            if response.data:
                license_info = response.data[0]
                expiry_date_str = license_info.get('expiry_date')
                
                expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                
                if datetime.date.today() <= expiry_date:
                    # Lisensi valid
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "valid": True, 
                        "message": f"Lisensi aktif hingga {expiry_date.strftime('%d %B %Y')}"
                    }).encode())
                else:
                    # Lisensi kedaluwarsa
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "valid": False, 
                        "message": f"Lisensi sudah kedaluwarsa pada {expiry_date.strftime('%d %B %Y')}"
                    }).encode())
            else:
                # Kunci tidak ditemukan
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"valid": False, "message": "Kunci lisensi tidak valid."}).encode())

        except Exception as e:
            print(f"Error saat validasi: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"valid": False, "message": "Terjadi error di server."}).encode())
        
        return
