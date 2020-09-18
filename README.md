# uPtt client server

### 這是在使用者端執行的伺服器，負責整合 PTT 還有 app server 與前端之間的溝通。

## 版本
#### 0.0.1 beta

## 編譯
#### 請先 clone [uPtt](https://github.com/uPtt-messenger/uPtt) and submodules([backend_util](https://github.com/uPtt-messenger/backend_util), [client-server](https://github.com/uPtt-messenger/client-server))
```batch
cd uPtt/client-server
pip install -r requirements.txt
pip install pyinstaller

cd ..
pyinstaller client-server.spec
```

## 後端開發成員
#### CodingMan (CodingMan@uptt.cc)
