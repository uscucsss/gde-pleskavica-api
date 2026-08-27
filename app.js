
async function loadCafes() {
    try {
        const response = await fetch('http://127.0.1:8000/cafes');

        

        const cafes = await response.json(); 
        const grid = document.getElementById('cafes-grid');
        grid.innerHTML = ''; 

        cafes.forEach(cafe => {
            
            let menuHTML = '';
            cafe.menu.forEach(dish => {
                menuHTML += `
                    <li class="menu-item">
                        <span>${dish.title}</span>
                        <strong>${dish.price} RSD</strong>
                    </li>
                `;
            });

            const card = document.createElement('div');
            card.className = 'cafe-card'; 
            card.innerHTML = `
                <h2>${cafe.name}</h2>
                <p>📍 ${cafe.address}</p>
                <h3>Меню:</h3>
                <ul class="menu-list">
                    ${menuHTML}
                </ul>
            `;
            grid.appendChild(card);
        });

    } catch (error) {
        console.error("Ошибка при работе с API:", error);
        document.getElementById('cafes-grid').innerHTML = `
            <p style="color: red; font-weight: bold;">
                Не удалось связаться с сервером. Проверь, запущен ли твой FastAPI в терминале!
            </p>
        `;
    }
}
window.onload = loadCafes;