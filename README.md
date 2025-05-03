Setup :
1. install ubuntu atau jenis nya.
2. sudo git clone https://github.com/KevinAprianto13/Managment-Switch-via-Automation-with-Python.git
   ![download script](https://github.com/user-attachments/assets/00ebd459-eb63-456a-a76f-e9f9a9f5ee4f)
3. cd Managmenet-Switch-via-Automation-with-Python
   ![masuk ke diretory yang sudah di download](https://github.com/user-attachments/assets/a8673570-620b-4fce-8d7b-f05796c9e9e2)
4. pip install netmiko jika blm terinstall
   ![download dan install netmiko sebagai library yangg di dukung untuk menjalankan script](https://github.com/user-attachments/assets/ffcce5d1-c0b9-4c45-a559-ac55ac8b2f00)
5. sudo nano ~/.bashrc
   python3 /home/kevin/Managmenet/app.py (tambahkan di bagian akhir dari barisan)
   ![auto run](https://github.com/user-attachments/assets/6ceae8b7-4e57-40fc-90c1-69950056c165)
6. source ~/.bashrc
7. python3 app.py (optional, manual menjalankan script nya)
8. buka tab terminal baru untuk pengetesan autorun yang sudah di setup tersebut.
9. selanjut setup by gns3 untuk simulasi nya atau jika punya real device bisa di simulasikan.
    ![topology](https://github.com/user-attachments/assets/491d8ba8-495e-45d8-bf73-116b3eec3c51)
10. Buat vlan managment untuk remote dan vlan untuk internet di mikrotik
11. configurasi kan ssh pada cisco switch
12. buat vlan managment terlebih dahulu dan berikan ip yang di sesuai kan dengan vlan managment di mikrotik
    ![vlan managmenet ](https://github.com/user-attachments/assets/c8c04801-9843-4105-ae1e-84a4a98fb4cb)
13. berikan trunk ke interface switch yang mengarah ke mikrotik
    ![interface trunk](https://github.com/user-attachments/assets/da5599f6-9152-4306-9dfb-bb97c4297d36)
14. uji coba ping dari switch dengan ip remote managment dari mikroitk atau gateway dari ip vlan managment nya
15. jika berhasil, akses ip switch tersebut di script ini dan di sesuai dengan usernama password hasil dari ssh yang dibuat di switch
    jika device menolak connect 
    ![troubleshoot](https://github.com/user-attachments/assets/e7d508ef-fd37-408f-aaec-e5ff72b7c321)
    lalukan routing pada ubuntu nya
    sudo ip route (ip switch) via (ip mikrotik yang terkena nat dari vm)
    ![solved](https://github.com/user-attachments/assets/73a0d16d-8608-418d-91fe-2ed9ea074a85)
16. lalu coba kembali untuk memasukan ip switch dan ssh login nya kembali
    ![configurasi switch menggunakan script automation](https://github.com/user-attachments/assets/bc28280a-e54e-425b-97a8-433d14c31cc6)

