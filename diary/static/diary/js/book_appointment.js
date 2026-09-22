function selectSlot(date, time, btn) {
    // Перевіряємо, чи цей слот вже обраний
    const isAlreadySelected = btn.classList.contains('slot-selected');
    
    // Знімаємо виділення з усіх кнопок
    document.querySelectorAll('.slot-btn').forEach(b => {
        b.classList.remove('slot-selected');
    });
    
    // Очищаємо приховані поля
    document.getElementById('selected-date').value = '';
    document.getElementById('selected-time').value = '';
    
    // Якщо слот вже був обраний — знімаємо вибір і виходимо
    if (isAlreadySelected) {
        document.getElementById('selected-info').style.display = 'none';
        return;
    }
    
    // Інакше — виділяємо обрану
    btn.classList.add('slot-selected');
    
    // Записуємо в приховані поля
    document.getElementById('selected-date').value = date;
    document.getElementById('selected-time').value = time;
    
    // Показуємо інформацію
    document.getElementById('selected-text').textContent = date + ' о ' + time;
    document.getElementById('selected-info').style.display = 'block';
}