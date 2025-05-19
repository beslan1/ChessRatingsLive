document.addEventListener('DOMContentLoaded', () => {
    let players = [];
    let filteredPlayers = [];
    let totalFilteredPlayers = [];
    let currentPage = 1;
    let playersPerPage = 30;
    let isTop100 = false;
    let isWomenFilter = false;
    let isChildrenFilter = false;
    let isSearching = false;
    let currentRatingFilter = 'fshr-classic'; // Дефолт: ФШР Классика
    let sortDirection = {}; // Для отслеживания направления сортировки

    const getElement = (id) => {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Элемент с ID "${id}" не найден`);
        }
        return element;
    };

    const updateTimeElement = getElement('update-time');
    const updateTime = () => {
        const now = new Date();
        const currentHours = now.getHours();
        const currentMinutes = now.getMinutes();
        const currentDay = now.getDate();
        const currentMonth = now.getMonth();
        const currentYear = now.getFullYear();

        let lastUpdate;
        if (currentHours < 8 || (currentHours === 8 && currentMinutes < 0)) {
            lastUpdate = new Date(currentYear, currentMonth, currentDay - 1, 20, 0);
        } else if (currentHours < 20 || (currentHours === 20 && currentMinutes < 0)) {
            lastUpdate = new Date(currentYear, currentMonth, currentDay, 8, 0);
        } else {
            lastUpdate = new Date(currentYear, currentMonth, currentDay, 20, 0);
        }

        const options = { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' };
        const formattedTime = lastUpdate.toLocaleString('ru-RU', options);

        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 1);
        const tomorrow = new Date(today);
        tomorrow.setDate(today.getDate() + 1);

        let dayPrefix = 'Сегодня';
        if (lastUpdate.getDate() === yesterday.getDate() && lastUpdate.getMonth() === yesterday.getMonth()) {
            dayPrefix = 'Вчера';
        } else if (lastUpdate.getDate() === tomorrow.getDate() && lastUpdate.getMonth() === tomorrow.getMonth()) {
            dayPrefix = 'Завтра';
        }

        if (updateTimeElement) {
            updateTimeElement.textContent = `${dayPrefix}, ${formattedTime}`;
        }
    };
    updateTime();

    // Показать лоадер перед загрузкой данных
    function showLoader() {
        const tbody = getElement('players-table');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="py-3 px-6 text-center text-gray-500">Загрузка данных...</td></tr>';
        }
    }

    showLoader();
    fetch('/api/players')
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (!Array.isArray(data)) throw new Error('Данные от сервера не являются массивом');
            players = data;
            console.log('Полученные игроки:', players);
            applyFilters();
            // После загрузки данных ищем Мукожева Беслана Валерьяновича и отображаем его
            const mukozhev = players.find(player => player.name === "Мукожев Беслан Валерьянович");
            if (mukozhev) {
                updatePlayerCard(mukozhev);
            } else {
                console.warn('Игрок "Мукожев Беслан Валерьянович" не найден в данных');
            }
        })
        .catch(error => {
            console.error('Ошибка загрузки данных:', error);
            const tbody = getElement('players-table');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="6" class="py-3 px-6 text-center text-red-500">Ошибка загрузки данных. Пожалуйста, попробуйте позже.</td></tr>';
            }
        });

    function renderTable() {
        const tbody = getElement('players-table');
        if (!tbody) {
            console.error('Таблица "players-table" не найдена');
            return;
        }

        tbody.innerHTML = '';
        if (!Array.isArray(filteredPlayers)) {
            console.error('filteredPlayers не является массивом:', filteredPlayers);
            tbody.innerHTML = '<tr><td colspan="6" class="py-3 px-6 text-center text-gray-500">Нет данных для отображения</td></tr>';
            return;
        }

        if (filteredPlayers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="py-3 px-6 text-center text-gray-500">Нет игроков, соответствующих фильтру</td></tr>';
            return;
        }

        const start = (currentPage - 1) * playersPerPage;
        const end = start + playersPerPage;
        const displayPlayers = filteredPlayers.slice(start, end);

        displayPlayers.forEach((player, index) => {
            if (!player || !player.id) {
                console.warn('Некорректные данные игрока:', player);
                return;
            }

            const globalIndex = start + index + 1;
            const ratingField = getRatingField(currentRatingFilter);
            const ratingDisplay = player[ratingField] === "" || !player[ratingField] ? "—" : player[ratingField];
            const genderIcon = player.gender === 'female'
                ? '<i class="fas fa-venus text-pink-400 text-sm ml-1"></i>'
                : '<i class="fas fa-mars text-blue-400 text-sm ml-1"></i>';
            const childLabel = player.isChild
                ? '<span class="ml-1 bg-yellow-200 text-yellow-900 text-xs font-medium px-2 py-0.5 rounded-full">Дети</span>'
                : '';
            // Корона отображается только для ФШР-фильтров и соответствующего типа чемпионства
            let isChampion = false;
            if (currentRatingFilter === 'fshr-classic' && player.is_classic_champion) {
                isChampion = true;
            } else if (currentRatingFilter === 'fshr-rapid' && player.is_rapid_champion) {
                isChampion = true;
            } else if (currentRatingFilter === 'fshr-blitz' && player.is_blitz_champion) {
                isChampion = true;
            }
            const championIcon = isChampion
                ? '<i class="fas fa-crown text-yellow-500 text-base ml-2"></i>' // Увеличиваем размер (text-base) и отступ (ml-2)
                : '';

            const row = document.createElement('tr');
            row.style.backgroundColor = globalIndex % 2 === 1 ? '#ffffff' : '#f5f5f5';
            row.className = `hover:bg-gray-50 cursor-pointer`;
            row.innerHTML = `
                <td class="py-3 px-6">${globalIndex}</td>
                <td class="py-3 px-6">${player.name || 'Не указано'}${genderIcon}${childLabel}${championIcon}</td>
                <td class="py-3 px-6">${player.title || '—'}</td>
                <td class="py-3 px-6">${ratingDisplay}</td>
                <td class="py-3 px-6" data-change="${player.change || '0'}">${player.change || '0'}</td>
                <td class="py-3 px-6">${player.age || '—'}</td>
            `;
            row.addEventListener('click', () => {
                console.log('Клик по строке, игрок:', player.name, 'ID:', player.id, 'Данные:', JSON.stringify(player));
                updatePlayerCard(player);
            });
            tbody.appendChild(row);
        });

        const shownFrom = getElement('shown-from');
        const shownTo = getElement('shown-to');
        const totalCount = getElement('total-count');
        if (shownFrom) shownFrom.textContent = start + 1;
        if (shownTo) shownTo.textContent = Math.min(end, filteredPlayers.length);
        if (totalCount) totalCount.textContent = filteredPlayers.length;
    }

    function renderPagination() {
        const pagination = getElement('pagination');
        if (!pagination) return;

        pagination.innerHTML = '';
        const pageCount = Math.ceil(filteredPlayers.length / playersPerPage);

        const prevButton = document.createElement('button');
        prevButton.className = `px-3 py-1 rounded-lg ${currentPage === 1 ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`;
        prevButton.textContent = 'Предыдущая';
        prevButton.disabled = currentPage === 1;
        prevButton.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderTable();
                renderPagination();
            }
        });
        pagination.appendChild(prevButton);

        for (let i = 1; i <= pageCount; i++) {
            const pageButton = document.createElement('button');
            pageButton.className = `px-3 py-1 rounded-lg ${i === currentPage ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`;
            pageButton.textContent = i;
            pageButton.addEventListener('click', () => {
                currentPage = i;
                renderTable();
                renderPagination();
            });
            pagination.appendChild(pageButton);
        }

        const nextButton = document.createElement('button');
        nextButton.className = `px-3 py-1 rounded-lg ${currentPage === pageCount ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`;
        nextButton.textContent = 'Следующая';
        nextButton.disabled = currentPage === pageCount;
        nextButton.addEventListener('click', () => {
            if (currentPage < pageCount) {
                currentPage++;
                renderTable();
                renderPagination();
            }
        });
        pagination.appendChild(nextButton);
    }

    function updatePlayerCard(player) {
        console.log('Запуск updatePlayerCard, данные:', JSON.stringify(player, null, 2));
        if (!player) {
            console.error('Игрок не передан в updatePlayerCard');
            return;
        }

        const playerCard = getElement('player-card');
        if (playerCard) {
            playerCard.classList.remove('active');
            setTimeout(() => playerCard.classList.add('active'), 10);
        } else {
            console.error('Элемент "player-card" не найден');
        }

        const set = (id, text) => {
            const el = getElement(id);
            if (el) {
                console.log(`Обновление элемента ${id}: ${text}`);
                el.textContent = text;
            } else {
                console.warn(`Элемент с ID "${id}" не найден в updatePlayerCard`);
            }
        };

        set('player-name', player.name || 'Не указано');
        set('player-title', player.title || '—');
        set('player-birth-year', player.age ? (2025 - player.age) : '—');
        set('player-gender', player.gender === 'female' ? 'Женский' : 'Мужской');
        set('player-fshr-classic', player.rating || '—');
        set('player-fshr-rapid', player.rapid_rating || '—');
        set('player-fshr-blitz', player.blitz_rating || '—');
        set('player-fide-classic', player.fide_rating || '—');
        set('player-fide-rapid', player.fide_rapid || '—');
        set('player-fide-blitz', player.fide_blitz || '—');
        set('player-tournaments', player.tournamentsPlayed || '0');
        set('player-best-result', player.bestResult || '—');
        set('player-last-tournaments', player.lastTournaments?.join(', ') || '—');
    }

    function updateStats() {
        const totalPlayers = getElement('total-players');
        const bestProgress = getElement('best-progress');
        const topRating = getElement('top-rating');

        if (!totalFilteredPlayers.length) {
            if (totalPlayers) totalPlayers.textContent = '0';
            if (bestProgress) bestProgress.textContent = '+0';
            if (topRating) topRating.textContent = '—';
            return;
        }

        if (totalPlayers) totalPlayers.textContent = totalFilteredPlayers.length;
        if (bestProgress) {
            const max = filteredPlayers.reduce((m, p) => Math.max(m, parseInt(p.change) || 0), 0);
            bestProgress.textContent = `+${max}`;
        }
        if (topRating) {
            const ratingField = getRatingField(currentRatingFilter);
            const rating = filteredPlayers[0]?.[ratingField];
            topRating.textContent = rating || '—';
        }
    }

    function getRatingField(filter) {
        const ratingFields = {
            'fshr-classic': 'rating',
            'fshr-rapid': 'rapid_rating',
            'fshr-blitz': 'blitz_rating',
            'fide-classic': 'fide_rating',
            'fide-rapid': 'fide_rapid',
            'fide-blitz': 'fide_blitz'
        };
        return ratingFields[filter] || 'rating';
    }

    function applyFilters() {
        isSearching = false;
        playersPerPage = isTop100 ? 100 : 30;

        totalFilteredPlayers = [...players];
        if (isWomenFilter) totalFilteredPlayers = totalFilteredPlayers.filter(p => p.gender === 'female');
        if (isChildrenFilter) totalFilteredPlayers = totalFilteredPlayers.filter(p => p.isChild);

        filteredPlayers = [...totalFilteredPlayers];
        const ratingField = getRatingField(currentRatingFilter);
        filteredPlayers.sort((a, b) => (parseInt(b[ratingField]) || 0) - (parseInt(a[ratingField]) || 0));

        if (!isTop100 && !isSearching) filteredPlayers = filteredPlayers.slice(0, playersPerPage);

        currentPage = 1;
        renderTable();
        updateStats();
        renderPagination();
    }

    function handleSearch() {
        const searchTerm = getElement('search')?.value.toLowerCase() || '';
        const ratingTerm = getElement('rating-search')?.value || '';

        isSearching = !!(searchTerm || ratingTerm);
        totalFilteredPlayers = [...players];

        if (searchTerm) {
            totalFilteredPlayers = totalFilteredPlayers.filter(p => p.name.toLowerCase().includes(searchTerm));
        }

        if (ratingTerm) {
            const ratingField = getRatingField(currentRatingFilter);
            totalFilteredPlayers = totalFilteredPlayers.filter(p => {
                const rating = parseInt(p[ratingField]);
                return !isNaN(rating) && rating >= parseInt(ratingTerm);
            });
        }

        if (isWomenFilter) totalFilteredPlayers = totalFilteredPlayers.filter(p => p.gender === 'female');
        if (isChildrenFilter) totalFilteredPlayers = totalFilteredPlayers.filter(p => p.isChild);

        filteredPlayers = [...totalFilteredPlayers];
        const ratingField = getRatingField(currentRatingFilter);
        filteredPlayers.sort((a, b) => (parseInt(b[ratingField]) || 0) - (parseInt(a[ratingField]) || 0));

        if (isTop100 && !isSearching) filteredPlayers = filteredPlayers.slice(0, 100);

        currentPage = 1;
        renderTable();
        updateStats();
        renderPagination();
    }

    // Функция сортировки
    window.sortTable = function(column) {
        // Удаляем классы сортировки у всех заголовков
        document.querySelectorAll('#players-table th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });

        // Переключаем направление сортировки
        sortDirection[column] = !sortDirection[column];
        const direction = sortDirection[column] ? 1 : -1;

        // Добавляем класс для текущего заголовка
        const th = Array.from(document.querySelectorAll('#players-table th')).find(el => el.textContent.includes(column === 'index' ? '#' : column.toUpperCase()));
        if (th) {
            th.classList.add(direction === 1 ? 'sort-asc' : 'sort-desc');
        }

        filteredPlayers.sort((a, b) => {
            let valA = a[column], valB = b[column];
            if (column === 'rating') {
                valA = parseInt(a[getRatingField(currentRatingFilter)]) || 0;
                valB = parseInt(b[getRatingField(currentRatingFilter)]) || 0;
            } else if (column === 'change') {
                valA = parseInt(a.change) || 0;
                valB = parseInt(b.change) || 0;
            } else if (column === 'age') {
                valA = parseInt(a.age) || 0;
                valB = parseInt(b.age) || 0;
            } else if (column === 'index') {
                valA = filteredPlayers.indexOf(a);
                valB = filteredPlayers.indexOf(b);
            } else {
                valA = (valA || '').toString().toLowerCase();
                valB = (valB || '').toString().toLowerCase();
            }
            return direction * (valA > valB ? 1 : -1);
        });

        renderTable();
    };

    // Обработчики фильтров рейтинга
    const ratingFilters = [
        'fshr-classic', 'fshr-rapid', 'fshr-blitz',
        'fide-classic', 'fide-rapid', 'fide-blitz'
    ];

    ratingFilters.forEach(filter => {
        const btn = getElement(`filter-${filter}`);
        if (btn) {
            btn.addEventListener('click', () => {
                console.log(`Выбран фильтр: ${filter}`);
                currentRatingFilter = filter;
                ratingFilters.forEach(f => {
                    const otherBtn = getElement(`filter-${f}`);
                    if (otherBtn) {
                        otherBtn.classList.remove('active');
                    }
                });
                btn.classList.add('active');
                applyFilters();
            });
        }
    });

    // Установить дефолтный активный фильтр
    const defaultFilterBtn = getElement('filter-fshr-classic');
    if (defaultFilterBtn) {
        defaultFilterBtn.classList.add('active');
    }

    const allPlayersBtn = getElement('all-players');
    if (allPlayersBtn) {
        allPlayersBtn.addEventListener('click', () => {
            isTop100 = isWomenFilter = isChildrenFilter = false;
            ['top100', 'women', 'children'].forEach(id => {
                const btn = getElement(id);
                if (btn) {
                    btn.classList.remove('bg-blue-600', 'text-white');
                    btn.classList.add('bg-gray-200', 'text-gray-700');
                    if (id === 'top100') btn.textContent = 'Топ 100';
                }
            });
            applyFilters();
        });
    }

    const toggleBtn = (btn, state) => {
        btn.classList.toggle('bg-gray-200', !state);
        btn.classList.toggle('text-gray-700', !state);
        btn.classList.toggle('bg-blue-600', state);
        btn.classList.toggle('text-white', state);
    };

    const womenBtn = getElement('women');
    if (womenBtn) {
        womenBtn.addEventListener('click', () => {
            isWomenFilter = !isWomenFilter;
            isChildrenFilter = false;
            toggleBtn(womenBtn, isWomenFilter);
            toggleBtn(getElement('children'), false);
            applyFilters();
        });
    }

    const childrenBtn = getElement('children');
    if (childrenBtn) {
        childrenBtn.addEventListener('click', () => {
            isChildrenFilter = !isChildrenFilter;
            isWomenFilter = false;
            toggleBtn(childrenBtn, isChildrenFilter);
            toggleBtn(getElement('women'), false);
            applyFilters();
        });
    }

    const top100Btn = getElement('top100');
    if (top100Btn) {
        top100Btn.addEventListener('click', () => {
            isTop100 = !isTop100;
            top100Btn.textContent = isTop100 ? 'Топ 30' : 'Топ 100';
            toggleBtn(top100Btn, isTop100);
            applyFilters();
        });
    }

    const searchInput = getElement('search');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearch);
    }

    const ratingSearch = getElement('rating-search');
    if (ratingSearch) {
        ratingSearch.addEventListener('input', handleSearch);
    }
});