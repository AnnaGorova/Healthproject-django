from fastapi import FastAPI, HTTPException


app = FastAPI(title="Health API")

items = [
    {"id": 1, "name": "Аспірин", "dosage": "500mg", "purpose": "Знеболення"},
    {"id": 2, "name": "Парацетамол", "dosage": "200mg", "purpose": "Жарознижувальне"},
    {"id": 3, "name": "Ношпа", "dosage": "40mg", "purpose": "Спазмолітик"},
    {"id": 4, "name": "Ібупрофен", "dosage": "400mg", "purpose": "Протизапальне"},
    {"id": 5, "name": "Лоратадин", "dosage": "10mg", "purpose": "Протиалергічне"},
]

@app.get("/items")
def get_items():
    return items


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Препаоат не знайдено")