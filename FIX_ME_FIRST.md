# ⚠️ FIX_ME_FIRST.md — 3 cheezein jo aapko khud karni hain

Maine aapka poora project scan karke yeh fix kar diye hain:
1. ✅ `backend/requirements.txt` aur `frontend/requirements.txt` se `pandas==2.2.2`
   ka purana pinned version hata diya (yeh Windows Python 3.13 par build error
   deta tha) — ab flexible version use hoga jo aapke system ke liye ready-made
   wheel dhoondh lega.
2. ✅ Purani `venv` folders aur `__pycache__` clutter hata diya (yeh zip me
   nahi hone chahiye thay — inhe har machine par dobara banana padta hai).
3. ✅ `.env` file ki line-endings fix ki (Windows CRLF issue) aur `frontend/.env`
   bhi bana di (pehle sirf root aur backend me thi).

## ❗ Yeh 1 cheez sirf AAP fix kar sakti hain (main nahi kar sakta):

`.env` file me yeh line hai:
```
MONGO_URI=mongodb+srv://<db_username>:PASSWORD@cluster0.uilsdxd.mongodb.net/...
```

`<db_username>` **literal placeholder text** hai — yeh kabhi replace hi nahi
hua asli username se. Yehi wajah hai `bad auth: authentication failed` error ki.

### Fix karne ka tareeqa:
1. https://cloud.mongodb.com par login karein
2. Left sidebar → **Database Access**
3. Apna database user dhoondhein — us user ka **exact username** copy karein
   (yeh aapke Atlas login email se **alag** hota hai, yeh sirf database ke
   liye banaya gaya separate user hai)
4. `.env`, `backend/.env`, aur `frontend/.env` — **teenon files** me
   `<db_username>` ko us asli username se replace karein (angle brackets
   `< >` bhi hata dein)

Example — agar aapka database username `nimbus_admin` hai, to line yeh banegi:
```
MONGO_URI=mongodb+srv://nimbus_admin:vAL4VBxxlRvAwOLy@cluster0.uilsdxd.mongodb.net/?appName=Cluster0
```

**Agar password bhool gayi hain:** Atlas → Database Access → apne user ke
saamne **Edit** → **Edit Password** → naya simple password set karein
(sirf letters/numbers, koi `@ # $ :` na ho).

## ⚠️ Ek aur cheez check karein

Aapki `.env` me `OPENAI_API_KEY` yeh format me hai: `AQ.Ab8RN6LRz...`

OpenAI API keys aam taur par `AIzaSy...` se shuru hoti hain aur
~39 characters ki hoti hain. Yeh key us format se match nahi kar rahi —
ho sakta hai yeh galat/expired key ho. Confirm karne ke liye:
https://aistudio.google.com/app/apikey par jayein, apni key dobara copy
karein, aur `.env` (teenon jagah) me update kar dein.

---

## Ab yeh steps chalayein (order me):

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m app.seed_admin
uvicorn app.main:app --reload --port 8000
```

Naya terminal:
```cmd
cd frontend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
