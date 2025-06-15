document.addEventListener('DOMContentLoaded', () => {
    let players = [];
    let filteredPlayers = []; 
    let totalFilteredPlayers = []; 
    let tournaments = [];
    let currentPage = 1;
    let playersPerPage = 20; 
    let allAchievers = [];
    
    let isTop100Filter = false;
    let isWomenFilter = false;
    let isChildrenFilter = false;
    let isSearching = false;
    let isTournamentTable = false; 
    let lastSelectedTournamentId = null;
    let playerAForComparison = null;
    let fullChampionHistory = [];
    let currentChampionFilter = 'Все';

    let currentRatingFilter = 'fshr-classic';
    let sortDirection = {};
    let originalTableHeader = '';
    let currentTournamentDetails = null; 

    const RATING_FILTER_BUTTON_IDS = [
        'filter-fshr-classic', 'filter-fshr-rapid', 'filter-fshr-blitz',
        'filter-fide-classic', 'filter-fide-rapid', 'filter-fide-blitz'
    ];

    const getElement = (id) => {
        const element = document.getElementById(id);
        if (!element) console.warn(`getElement_WARN: Элемент с ID '${id}' не найден!`);
        return element;
    };

    // ✅ Получаем новые элементы для сравнения
    const compareBtn = getElement('compare-player-btn');
    const comparisonModal = getElement('comparison-modal');
    const comparisonSearchInput = getElement('comparison-search-input');
    const comparisonSearchResults = getElement('comparison-search-results');
    const comparisonCancelBtn = getElement('comparison-cancel');
    const comparisonView = getElement('comparison-view');
    const tableContainer = getElement('table-container');

    const mainBannerImg = document.querySelector('img.header-banner');
    
    const playerViewCardsEl = getElement('player-view-cards'); 
    const playerCardEl = getElement('player-card');
    const tournamentSummaryCardEl = getElement('tournament-summary-card');

    if (!playerViewCardsEl) console.error("КРИТИЧЕСКАЯ ОШИБКА: Элемент #player-view-cards не найден!");
    if (!tournamentSummaryCardEl) console.error("КРИТИЧЕСКАЯ ОШИБКА: Элемент #tournament-summary-card не найден!");

    // ... (весь ваш существующий код до самого конца, без изменений) ...
    // Станет:
// ЗАМЕНИТЕ НА ЭТУ ВЕРСИЮ

    
          // Эта функция теперь ЕДИНСТВЕННАЯ отвечает за то, что показано в правой колонке
// ЗАМЕНА №1: НОВАЯ, УПРОЩЕННАЯ ФУНКЦИЯ
// ✅ ЭТО ЕДИНСТВЕННОЕ ИЗМЕНЕНИЕ, КОТОРОЕ НУЖНО СДЕЛАТЬ
// ✅ ФИНАЛЬНАЯ ВЕРСИЯ. Используем прямое управление стилями.
// ЗАМЕНИТЕ ВАШУ ФУНКЦИЮ НА ЭТУ ВЕРСИЮ
// ✅ ФИНАЛЬНАЯ ВЕРСИЯ. Объединяем два рабочих подхода.
function updateRightColumnView(viewName, data = null) {
    // СНАЧАЛА ПРОВЕРЯЕМ, НЕ В РЕЖИМЕ ЛИ МЫ ТУРНИРА
    const isTournamentMode = document.body.classList.contains('tournament-view-active');

    const topAchieversContainer = getElement('top-achievers-container');
    const playerCard = getElement('player-card');

    if (!topAchieversContainer || !playerCard) {
        console.error("Не найден контейнер Топ-10 или карточки игрока.");
        return;
    }

    // --- Логика для обычного режима ---
    // Эти команды будут выполняться, ТОЛЬКО ЕСЛИ мы НЕ в режиме турнира
    if (!isTournamentMode) {
        if (viewName === 'PLAYER_CARD') {
            topAchieversContainer.style.display = 'none';
            playerCard.style.display = 'flex';
        } else if (viewName === 'DEFAULT') {
            topAchieversContainer.style.display = 'block';
            playerCard.style.display = 'none';
        }
    }

    // --- Логика заполнения данных (работает всегда) ---
    if (viewName === 'PLAYER_CARD') {
        updatePlayerCard(data); 
    } else if (viewName === 'DEFAULT') {
        updatePlayerCard(null); 
    } else if (viewName === 'TOURNAMENT_SUMMARY') {
        if (data && data.highlights) {
            displayTournamentSummary(data.highlights, data.results);
        }
    }
}
/**
 * Эта функция принудительно устанавливает правильный вид для режима турнира,
 * скрывая все карточки в правой колонке, кроме сводки по турниру.
 * Она вызывается в конце загрузки турнира, чтобы переопределить любые другие стили.
 */
function forceTournamentViewLayout() {
    console.log('%c[FORCE_VIEW] Принудительное применение стилей для режима турнира...', 'color: red; font-weight: bold;');
    
    const topAchieversContainer = getElement('top-achievers-container');
    const playerCard = getElement('player-card');
    const championsCard = getElement('champions-card');
    const footerContainer = document.querySelector('.footer-container');
    const tournamentSummaryCard = getElement('tournament-summary-card');

    // Принудительно прячем все, что не нужно
    if (topAchieversContainer) {
        topAchieversContainer.style.display = 'none';
    }
    if (playerCard) {
        playerCard.style.display = 'none';
    }
    if (championsCard) {
        championsCard.style.display = 'none';
    }
    if (footerContainer) {
        footerContainer.style.display = 'none';
    }

    // Принудительно показываем то, что нужно.
    // CSS-класс 'd-none' от Bootstrap может мешать, поэтому используем 'flex'.
    if (tournamentSummaryCard) {
        tournamentSummaryCard.classList.remove('d-none'); // На всякий случай
        tournamentSummaryCard.style.display = 'flex';     // Устанавливаем display: flex
    }
}
    const showLoader = () => { const tbody = getElement('players-table'); if (tbody) { tbody.innerHTML = '<tr><td colspan="6" class="py-3 px-4 text-center text-gray-600">Загрузка...</td></tr>'; } };
    
    async function loadPlayers() { 
        try {
            const response = await fetch('/api/players');
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            players = await response.json();
            const tableHeader = getElement('table-header');
            if (tableHeader && !originalTableHeader && !isTournamentTable) { 
                originalTableHeader = tableHeader.innerHTML;
            }
            if (!isTournamentTable) applyFilters(); 
        } catch (error) {
            console.error('loadPlayers: Ошибка загрузки игроков:', error);
            const tbody = getElement('players-table');
            if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="py-3 px-4 text-center text-red-500">Ошибка загрузки игроков</td></tr>';
        }
    }
    async function loadAllAchievers() {
    try {
        const response = await fetch('/api/all-achievers');
        if (!response.ok) throw new Error(`HTTP error!`);
        allAchievers = await response.json();
    } catch (error) {
        console.error('loadAllAchievers: Ошибка загрузки всех достижений:', error);
    }
}
    
    async function loadTournamentsData() { 
        try {
            const response = await fetch('/api/tournaments');
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            tournaments = await response.json();
        } catch (error) {
            console.error('loadTournamentsData: Ошибка загрузки турниров:', error);
            tournaments = [];
        }
    }
    // ✅ НАЧАЛО: НОВЫЕ ФУНКЦИИ ДЛЯ ТОП-10
async function loadTopAchievers() {
    try {
        const response = await fetch('/api/top-achievers');
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const topPlayers = await response.json();
        renderTopAchievers(topPlayers);
    } catch (error) {
        console.error('loadTopAchievers: Ошибка загрузки топ-10:', error);
    }
}

// ✅ ФИНАЛЬНАЯ ВЕРСИЯ ОТОБРАЖЕНИЯ ТОП-10
function renderTopAchievers(players) {
    const container = getElement('top-achievers-container');
    if (!container) return;

    const tooltipText = "Очки начисляются за призовые места. \nКрупные турниры (Чемпионат, Первенство, Кубок КБР)\nприносят больше очков, чем остальные.";
    
    let html = `
        <div style="position: relative; text-align: center; margin-bottom: 0.5rem;">
            <h3 style="margin: 0; font-size: 1.25rem; font-weight: 600; display: inline-block;">
                Топ-10
                <span title="${tooltipText}" style="cursor: help; font-weight: normal;">ℹ️</span>
            </h3>
            <button id="show-all-achievers-btn" style="position: absolute; right: 0; top: 50%; transform: translateY(-50%); font-size: 0.875rem; font-weight: 500; color: #3b82f6; background: none; border: none; padding: 0; cursor: pointer;">Все</button>
        </div>
        <ol>`;
    
    players.forEach(player => {
        let abbreviatedName = player.name;
        const nameParts = player.name.split(' ');
        
        if (nameParts.length > 1) {
            const lastName = nameParts[0];
            const firstNameInitial = nameParts[1].charAt(0);
            abbreviatedName = `${lastName} ${firstNameInitial}.`;
        }

        html += `
            <li>
                <span class="achiever-name">${abbreviatedName}</span>
                <div class="achiever-medals">
                    <span class="font-bold">${player.points}</span> 
                    <span class="medal-count">🥇 ${player.gold}</span>
                    <span class="medal-count">🥈 ${player.silver}</span>
                    <span class="medal-count">🥉 ${player.bronze}</span>
                </div>
            </li>
        `;
    });

    html += '</ol>';
    container.innerHTML = html;
}
// Эту новую функцию можно добавить после функции renderTopAchievers
function displayAllAchievers() {
        console.log("Отображение полного рейтинга достижений...");
        showLoader();

        const tableHeader = getElement('table-header');
        const tbody = getElement('players-table');
        if (!tableHeader || !tbody) return;

        // Сброс видов
        document.body.classList.remove('tournament-view-active');
        if (comparisonView) comparisonView.classList.add('hidden');
        if (tableContainer) tableContainer.classList.remove('hidden');
        updateRightColumnView('DEFAULT');
        
        tableHeader.innerHTML = `
            <tr><th colspan="7" class="py-3 px-2 text-xl text-center font-bold">Общий зачет по очкам достижений</th></tr>
            <tr class="uppercase text-base leading-normal">
                <th class="py-3 px-2 text-center">#</th>
                <th class="py-3 px-2 text-left">Ф И О</th>
                <th class="py-3 px-2 text-center font-bold">Зачетные очки</th>
                <th class="py-3 px-2 text-center">Турнирные очки</th>
                <th class="py-3 px-2 text-center">🥇</th>
                <th class="py-3 px-2 text-center">🥈</th>
                <th class="py-3 px-2 text-center">🥉</th>
            </tr>
        `;

        tbody.innerHTML = '';
        
        // Вот проверка, которую вы искали.
        // Она проверяет, удалось ли функции loadAllAchievers загрузить данные.
        if (!allAchievers || allAchievers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-red-500">Данные о достижениях не загружены или отсутствуют.</td></tr>';
            getElement('pagination').innerHTML = '';
            getElement('filter-info').textContent = `Всего: 0`;
            return;
        }

        allAchievers.forEach((player, index) => {
            const row = document.createElement('tr');
            row.className = `${index % 2 === 0 ? 'even-row' : 'odd-row'}`;
            row.innerHTML = `
                <td class="py-3 px-2 text-center">${index + 1}</td>
                <td class="py-3 px-2 text-left">${player.name}</td>
                <td class="py-3 px-2 text-center font-bold">${player.points}</td>
                <td class="py-3 px-2 text-center">${player.raw_points}</td>
                <td class="py-3 px-2 text-center">${player.gold}</td>
                <td class="py-3 px-2 text-center">${player.silver}</td>
                <td class="py-3 px-2 text-center">${player.bronze}</td>
            `;
            tbody.appendChild(row);
        });

        getElement('pagination').innerHTML = '';
        getElement('filter-info').textContent = `Всего: ${allAchievers.length}`;
    }

function displayChampionHistory() {
    // Эта вспомогательная функция будет рисовать саму таблицу
    const renderFilteredHistory = () => {
        const tbody = getElement('players-table');
        if (!tbody) return;

        let dataToRender = fullChampionHistory;

        // Применяем фильтр, если он не 'Все'
        if (currentChampionFilter !== 'Все') {
    dataToRender = fullChampionHistory.filter(entry => {
        if (currentChampionFilter === 'Кубки') return entry.event.includes('Кубок');
        if (currentChampionFilter === 'г. Нальчик') return entry.event.includes('Нальчик');
        if (currentChampionFilter === 'Ветераны') return entry.group === 'Ветераны'; // ✅ ВОТ ИСПРАВЛЕНИЕ
        return entry.discipline === currentChampionFilter;
    });
}

        tbody.innerHTML = '';
        if (!dataToRender || dataToRender.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4">Записи не найдены</td></tr>`;
            return;
        }

        dataToRender.forEach((entry, index) => {
            const row = document.createElement('tr');
            row.className = `${index % 2 === 0 ? 'even-row' : 'odd-row'}`;
            let categoryDisplay = entry.discipline || '';
            if (entry.group && entry.group !== 'Общий') {
                categoryDisplay += ` (${entry.group})`;
            }
            row.innerHTML = `
                <td class="py-3 px-2 text-center font-semibold">${entry.year || '—'}</td>
                <td class="py-3 px-2 text-left">${entry.event || '—'}</td>
                <td class="py-3 px-2 text-left">${categoryDisplay || '—'}</td>
                <td class="py-3 px-2 text-left font-bold">${entry.champion || '—'}</td>
            `;
            tbody.appendChild(row);
        });
        
        getElement('filter-info').textContent = `Всего записей: ${dataToRender.length}`;
    };

    // --- Основная логика функции ---
    console.log("Загрузка истории чемпионов...");
    showLoader(); 

    fetch('/api/past-champions')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(history => {
            fullChampionHistory = history.sort((a, b) => b.year - a.year); // Загружаем и сортируем данные один раз
            currentChampionFilter = 'Все'; // Сбрасываем фильтр по умолчанию

            const tableContainer = document.getElementById('table-container');
            const tableHeader = getElement('table-header');
            if (!tableHeader || !tableContainer) return;
            
            document.body.classList.remove('tournament-view-active');
            if (comparisonView) comparisonView.classList.add('hidden');
            if (tableContainer) tableContainer.classList.remove('hidden');
            updateRightColumnView('DEFAULT');
            tableContainer.classList.remove('history-view-active'); // Убираем горизонтальный скролл

            // Создаем HTML для кнопок-фильтров
            const filters = ['Все', 'Классика', 'Рапид', 'Блиц', 'Кубки', 'г. Нальчик', 'Ветераны'];
            const filterButtonsHTML = filters.map(f => 
                `<button class="history-filter-btn" data-filter="${f}">${f}</button>`
            ).join('');

            tableHeader.innerHTML = `
                <tr><th colspan="4" class="py-3 px-2 text-xl text-center font-bold">История Чемпионов</th></tr>
                <tr><th colspan="4" class="py-2"><div class="history-filters">${filterButtonsHTML}</div></th></tr>
                <tr class="uppercase text-base leading-normal">
                    <th class="py-3 px-2 text-center">Год</th>
                    <th class="py-3 px-2 text-left">Турнир</th>
                    <th class="py-3 px-2 text-left">Категория</th>
                    <th class="py-3 px-2 text-left">🥇 Чемпион</th>
                </tr>
            `;

            // Устанавливаем активную кнопку
            document.querySelector(`.history-filter-btn[data-filter="Все"]`).classList.add('active');
            
            // Первая отрисовка таблицы
            renderFilteredHistory();

            // Добавляем обработчик событий на контейнер с кнопками
            const filtersContainer = tableHeader.querySelector('.history-filters');
            if (filtersContainer) {
                filtersContainer.addEventListener('click', (e) => {
                    if (e.target.classList.contains('history-filter-btn')) {
                        currentChampionFilter = e.target.dataset.filter;
                        
                        // Обновляем активную кнопку
                        tableHeader.querySelectorAll('.history-filter-btn').forEach(btn => btn.classList.remove('active'));
                        e.target.classList.add('active');

                        // Перерисовываем таблицу с новым фильтром
                        renderFilteredHistory();
                    }
                });
            }

            getElement('pagination').innerHTML = ''; // Убираем пагинацию
        })
        .catch(error => {
            console.error('Ошибка при загрузке истории чемпионов:', error);
            const tbody = getElement('players-table');
            if(tbody) tbody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-red-500">Не удалось загрузить историю</td></tr>';
        });
}
// Этот код нужно добавить в конец файла, где все другие обработчики событий
document.addEventListener('click', function(event) {
    if (event.target && event.target.id === 'show-all-achievers-btn') {
        event.preventDefault(); // На всякий случай
        displayAllAchievers();
    }
});
    // ЗАМЕНИТЕ НА ЭТУ ВЕРСИЮ
const applyTheme = (themeName) => {
    const themeStyles = getElement('theme-styles');
    if (!themeStyles) {
        console.error("applyTheme: КРИТИЧЕСКАЯ ОШИБКА - Элемент <link id='theme-styles'> не найден!");
        return; 
    }
    
    // ✅ В themeMap больше нет placeholderSrc
    const themeMap = {
        'theme-art': { css: 'css/art.css', bannerSrc: mainBannerImg?.dataset.defaultSrc },
        'theme-roman': { css: 'css/roman.css', bannerSrc: mainBannerImg?.dataset.romanSrc },
        'theme-simple': { css: 'css/simple.css', bannerSrc: mainBannerImg?.dataset.simpleSrc },
        'theme-ocean': { 
            css: 'css/ocean.css', 
            bannerSrc: mainBannerImg?.dataset.oceanSrc || mainBannerImg?.dataset.defaultSrc
        }
    };
    
    let selectedTheme = themeMap[themeName]; 
    if (!selectedTheme) { 
        console.warn(`applyTheme: Тема "${themeName}" не найдена. Применена 'theme-art'.`);
        themeName = 'theme-art'; 
        selectedTheme = themeMap[themeName]; 
    }
    
    const newHref = `/static/${selectedTheme.css}?v=${new Date().getTime()}`; 
    themeStyles.setAttribute('href', newHref);
    
    document.body.classList.remove('theme-art', 'theme-roman', 'theme-simple', 'theme-ocean');
    document.body.classList.add(themeName);

    if (mainBannerImg && selectedTheme.bannerSrc) mainBannerImg.src = selectedTheme.bannerSrc;
    // ✅ Строка с placeholderImg полностью удалена

    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === themeName);
    });
    localStorage.setItem('selectedTheme', themeName);
};
    
    const displayTournamentSummary = (highlights, tournamentResults) => { 
    const contentEl = getElement('tournament-summary-content');
    if (!contentEl) {
        console.error("displayTournamentSummary: Элемент #tournament-summary-content не найден!");
        return;
    }
    console.log('[displayTournamentSummary] Получены highlights:', highlights);
    if (!highlights || Object.keys(highlights).length === 0) {
        console.warn('[displayTournamentSummary] Данные highlights пусты или отсутствуют');
        contentEl.innerHTML = '<p class="text-center text-red-500">Данные для сводки по турниру отсутствуют.</p>';
        return;
    }
        const icons = { 
            medal: 'fas fa-medal', performance: 'fas fa-chart-line',
            rating_gain: 'fas fa-arrow-alt-circle-up text-green-500', youngest: 'fas fa-baby',
            oldest: 'fas fa-user-tie', black_pieces: 'fas fa-chess-knight text-gray-700', 
            white_pieces: 'fas fa-chess-knight text-orange-400', upset: 'fas fa-bolt',
            avg_rating: 'fas fa-tachometer-alt', avg_age: 'fas fa-birthday-cake',
            draw_percent: 'fas fa-handshake'
        };

        const createSummaryItem = (iconClass, title, valueData) => {
            if (!valueData && valueData !== 0 && typeof valueData !== 'string') return ''; 
            let displayValueHtml = '';
            if (typeof valueData === 'object' && valueData !== null) {
                let textParts = [];
                if (valueData.name) textParts.push(valueData.name);
                if (valueData.performance) textParts.push(`(Rp: ${valueData.performance})`);
                if (valueData.change && valueData.change !== 0) textParts.push(`(${valueData.change > 0 ? '+' : ''}${valueData.change})`);
                if (valueData.age) textParts.push(`(${valueData.age} лет)`);
                if (valueData.percentage !== undefined) textParts.push(`(${valueData.percentage}%)`);
                if (valueData.score !== undefined && valueData.games !== undefined) textParts.push(`(${valueData.score} из ${valueData.games})`);
                let fullDisplayValue = textParts.join(' ');
                if (valueData.initial_rating) fullDisplayValue += ` <span class="text-xs text-gray-500">[${valueData.initial_rating}]</span>`;
                if (valueData.place) fullDisplayValue = `${valueData.place}. ${fullDisplayValue}`;
                displayValueHtml = `<span class="winner-value text-gray-900 dark:text-gray-100">${fullDisplayValue}</span>`;
            } else {
                 if (valueData === '' || valueData === null || valueData === undefined) return '';
                 displayValueHtml = `<span class="winner-value text-gray-900 dark:text-gray-100">${valueData}</span>`;
            }
            return `
                <div class="summary-item flex items-center py-1 border-b border-gray-200 dark:border-gray-700 last:border-b-0">
                    <i class="${iconClass} w-6 text-center mr-3 text-gray-600 dark:text-gray-400" style="font-size: 1.1em;"></i>
                    <span class="nomination-title font-medium mr-1 text-gray-700 dark:text-gray-300">${title}:</span>
                    ${displayValueHtml}
                </div>`;
        };

        let summaryHtml = '';
        if (highlights.top_3_finishers && highlights.top_3_finishers.length > 0) {
            summaryHtml += `<div class="mb-3"><strong class="block text-center text-md mb-1">Призеры:</strong>`;
            highlights.top_3_finishers.forEach((p, index) => {
                let medalColorClass = '';
                if (index === 0) medalColorClass = icons.medal + ' text-yellow-400'; 
                else if (index === 1) medalColorClass = icons.medal + ' text-gray-400'; 
                else if (index === 2) medalColorClass = icons.medal + ' text-yellow-600'; 
                summaryHtml += createSummaryItem(medalColorClass, '', {name: p.name, place: p.place, initial_rating: p.initial_rating, points: p.points});
            });
            summaryHtml += `</div>`;
        }
        
        if (highlights.top_3_performances && highlights.top_3_performances.length > 0) {
            summaryHtml += `<div class="mb-3"><strong class="block text-center text-md mb-1">Лучший перформанс (топ-3):</strong>`;
            highlights.top_3_performances.forEach((p, index) => {
                summaryHtml += createSummaryItem(icons.performance, `${index+1}. Rp: ${p.performance}`, {name: p.name, initial_rating: p.initial_rating});
            });
            summaryHtml += `</div>`;
        } else if (highlights.highest_performance_player && highlights.highest_performance_player.performance > 0) {
             summaryHtml += createSummaryItem(icons.performance, "Лучший перформанс", highlights.highest_performance_player);
        }

        if (highlights.top_3_rating_gains && highlights.top_3_rating_gains.length > 0) {
            summaryHtml += `<div class="mb-3"><strong class="block text-center text-md mb-1">Наибольший прирост рейтинга (топ-3):</strong>`;
            highlights.top_3_rating_gains.forEach((p, index) => {
                summaryHtml += createSummaryItem(icons.rating_gain, `${index+1}. ${p.change > 0 ? '+' : ''}${p.change}`, {name: p.name, initial_rating: p.initial_rating});
            });
            summaryHtml += `</div>`;
        } else if (highlights.max_rating_gain_player && highlights.max_rating_gain_player.change > 0) {
            summaryHtml += createSummaryItem(icons.rating_gain, "Макс. прирост рейтинга", highlights.max_rating_gain_player);
        }
        
        let generalStatsHtml = '<div class="mb-3"><strong class="block text-center text-md mb-1">Общая статистика:</strong>';
        let hasGeneralStats = false;
        if (highlights.avg_tournament_rating) { 
            generalStatsHtml += createSummaryItem(icons.avg_rating, "Средний рейтинг", Math.round(highlights.avg_tournament_rating));
            hasGeneralStats = true;
        }
        if (highlights.avg_participant_age) { 
            generalStatsHtml += createSummaryItem(icons.avg_age, "Средний возраст", `${Math.round(highlights.avg_participant_age)} лет`);
            hasGeneralStats = true;
        }
        if (highlights.draw_percentage !== undefined) { 
            generalStatsHtml += createSummaryItem(icons.draw_percent, "Процент ничьих", `${highlights.draw_percentage}%`);
            hasGeneralStats = true;
        }
        if (highlights.youngest_player) {
            generalStatsHtml += createSummaryItem(icons.youngest, "Самый юный", highlights.youngest_player);
            hasGeneralStats = true;
        }
        if (highlights.oldest_player) {
            generalStatsHtml += createSummaryItem(icons.oldest, "Самый возрастной", highlights.oldest_player);
            hasGeneralStats = true;
        }
        generalStatsHtml += '</div>';
        if(hasGeneralStats) summaryHtml += generalStatsHtml;

        if (highlights.best_white_player) {
            summaryHtml += createSummaryItem(icons.white_pieces, "Лучший результат белыми", highlights.best_white_player);
        }
        if (highlights.best_black_player) {
            summaryHtml += createSummaryItem(icons.black_pieces, "Лучший результат черными", highlights.best_black_player);
        }
        
        if (highlights.biggest_upset) {
            const upset = highlights.biggest_upset;
            let opponentDisplayName = null; 
            if (upset.defeated_opponent_seeding_num !== undefined && tournamentResults && tournamentResults.length > 0) {
                const opponentInResults = tournamentResults.find(r => 
                    String(r.seeding_number) === String(upset.defeated_opponent_seeding_num)
                );
                if (opponentInResults) {
                    opponentDisplayName = opponentInResults.name;
                }
            }
            let verb = "победил(а)"; 
            if (upset.upset_player_gender === 'male') {
                verb = "победил";
            } else if (upset.upset_player_gender === 'female') {
                verb = "победила";
            }
            const defeatedPlayerString = opponentDisplayName || `соперника №${upset.defeated_opponent_seeding_num}`;
            const upsetText = `${upset.upset_player_name} (${upset.upset_player_rating}) ${verb} ${defeatedPlayerString} (${upset.defeated_opponent_rating})`;
            summaryHtml += createSummaryItem(icons.upset, `Апсет (+${upset.rating_difference})`, upsetText);
        }
        contentEl.innerHTML = summaryHtml || '<p class="text-center">Дополнительная статистика по турниру недоступна.</p>';
    };

    showLoader(); 
    Promise.all([loadPlayers(), loadTournamentsData(), loadTopAchievers(), loadAllAchievers()]).then(() => {
        if (!isTournamentTable && filteredPlayers.length === 0 && players.length > 0) {
            applyFilters();
        // ...
    } else if (!isTournamentTable && players.length === 0){
        updateRightColumnView('DEFAULT'); // <--- ОДНО ИСПРАВЛЕНИЕ РЕШАЕТ ВСЕ
        getElement('players-table').innerHTML = '<tr><td colspan="6" class="py-3 px-4 text-center">Игроки не найдены.</td></tr>';
        updatePagination(0,0);
    }

    }).catch(error => {
        console.error("Promise.all: Ошибка при начальной загрузке данных:", error);
        const tbody = getElement('players-table');
        if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-red-500">Ошибка загрузки критических данных!</td></tr>';
        updateRightColumnView('DEFAULT'); // <--- ИСПРАВЛЕНИЕ
    });

    const renderTable = () => { 
        const tbody = getElement('players-table');
        const tableHeader = getElement('table-header');
        if (!tbody || !tableHeader) return;
        if (originalTableHeader && tableHeader.innerHTML !== originalTableHeader && !isTournamentTable) {
            tableHeader.innerHTML = originalTableHeader;
            if (typeof bindRatingFilterEvents === "function") bindRatingFilterEvents(); 
        }
        RATING_FILTER_BUTTON_IDS.forEach(id => getElement(id)?.classList.remove('active'));
        if (!isTournamentTable) getElement(`filter-${currentRatingFilter}`)?.classList.add('active');
        tbody.innerHTML = '';
        if (!Array.isArray(filteredPlayers) || !filteredPlayers.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="py-3 px-4 text-center">Нет игроков</td></tr>';
            updatePagination(0, 0);
            toggleRatingFilters(true);
            return;
        }
        playersPerPage = (isTop100Filter && !isTournamentTable) ? 100 : 20;
        const start = (currentPage - 1) * playersPerPage;
        const end = start + playersPerPage;
        const displayPlayers = filteredPlayers.slice(start, end);
        displayPlayers.forEach((player, index) => {
            if (!player || typeof player.id === 'undefined') { return; }
            const globalIndex = start + index + 1;
            const ratingField = getRatingField(currentRatingFilter);
            const ratingValue = player[ratingField];
            const ratingDisplay = ratingValue && ratingValue !== '—' && ratingValue !== 0 ? ratingValue : '—';
            const genderIcon = player.gender === 'female' ? '<i class="fas fa-venus ml-1 text-pink-500"></i>' : '';
            const childLabel = player.isChild ? '<i class="fas fa-child ml-1 text-yellow-500"></i>' : '';
            const isChamp = ( (currentRatingFilter === 'fshr-classic' && player.is_classic_champion) || (currentRatingFilter === 'fshr-rapid' && player.is_rapid_champion) || (currentRatingFilter === 'fshr-blitz' && player.is_blitz_champion) );
            const championIcon = isChamp ? '<i class="fas fa-crown ml-2"></i>' : '';
            let relevantChangeValue = 0;
            if (currentRatingFilter.startsWith('fshr-')) {
                if (currentRatingFilter === 'fshr-classic') relevantChangeValue = player.change_classic_value || 0;
                else if (currentRatingFilter === 'fshr-rapid') relevantChangeValue = player.change_rapid_value || 0;
                else if (currentRatingFilter === 'fshr-blitz') relevantChangeValue = player.change_blitz_value || 0;
            }
            const changeDisplay = relevantChangeValue === 0 ? '0' : (relevantChangeValue > 0 ? `+${relevantChangeValue}` : String(relevantChangeValue));
            const changeClass = relevantChangeValue > 0 ? 'rating-positive' : relevantChangeValue < 0 ? 'rating-negative' : '';
            const row = document.createElement('tr');
            row.className = `cursor-pointer player-row ${index % 2 === 0 ? 'even-row' : 'odd-row'}`;
            row.innerHTML = `<td class="py-3 px-2 text-center">${globalIndex}</td><td class="py-3 px-2">${player.name || '—'}${genderIcon}${childLabel}${championIcon}</td><td class="py-3 px-2 text-center">${player.title || '—'}</td><td class="py-3 px-2 text-center font-semibold">${ratingDisplay}</td><td class="py-3 px-2 text-center ${changeClass}">${changeDisplay}</td><td class="py-3 px-2 text-center">${player.age || '—'}</td>`;
            row.addEventListener('click', () => { updateRightColumnView('PLAYER_CARD', player); });
            tbody.appendChild(row);
        });
        updatePagination(start, end);
        toggleRatingFilters(true);
    };
    
  // ЗАМЕНИТЕ ВАШУ ФУНКЦИЮ renderTournamentTable НА ЭТУ ИСПРАВЛЕННУЮ ВЕРСИЮ
// ЗАМЕНА №2: ИСПРАВЛЕННАЯ ФУНКЦИЯ ДЛЯ ТАБЛИЦЫ ТУРНИРА (БЕЗ ONCLICK)
const renderTournamentTable = () => {
    const tbody = getElement('players-table');
    const tableHeader = getElement('table-header');
    if (!tbody || !tableHeader) return;

    isTournamentTable = true;
let titleHtml = '';

if (currentTournamentDetails?.name) {
    // --- Строка 1: Название и дата ---
    const nameAndDate = `${currentTournamentDetails.name}${currentTournamentDetails.date ? ` (${currentTournamentDetails.date})` : ''}`;

    // --- Строка 2: Звезды и средний рейтинг ---
    const stars = '⭐'.repeat(currentTournamentDetails.tier || 0);
    
    // Безопасно получаем средний рейтинг (он может отсутствовать)
    const avgRating = currentTournamentDetails.highlights?.avg_tournament_rating;
    const avgRatingText = avgRating ? `Средний рейтинг: ${Math.round(avgRating)}` : '';
    
    // Собираем вторую строку, только если в ней есть что показывать
    const detailsLine = [stars, avgRatingText].filter(Boolean).join(' | ');

    // --- Собираем финальный HTML с двумя строками ---
    titleHtml = `
        <tr>
            <th colspan="6" class="py-3 px-2 text-center tournament-title-header">
                <div style="font-weight: bold; font-size: 1.1em;">${nameAndDate}</div>
                ${detailsLine ? `<div style="font-weight: normal; font-size: 0.85em; margin-top: 4px; color:#ffffff;">${detailsLine}</div>` : ''}
            </th>
        </tr>
    `;
}

    // Убираем 'onclick' и добавляем 'data-sort-key'
    tableHeader.innerHTML = `
        ${titleHtml}
        <tr class="uppercase text-base leading-normal">
            <th class="py-3 px-2 text-center font-montserrat cursor-pointer" data-sort-key="place">Место</th>
            <th class="py-3 px-2 text-left font-montserrat cursor-pointer" data-sort-key="name">Фамилия Имя</th>
            <th class="py-3 px-2 text-center font-montserrat cursor-pointer" data-sort-key="points">Очки</th>
            <th class="py-3 px-2 text-center font-montserrat cursor-pointer" data-sort-key="initial_rating">R<sub>нач</sub></th>
            <th class="py-3 px-2 text-center font-montserrat cursor-pointer" data-sort-key="new_rating">R<sub>нов</sub></th>
            <th class="py-3 px-2 text-center font-montserrat cursor-pointer" data-sort-key="rating_change">+/-</th>
        </tr>`;

    // Безопасно навешиваем обработчики клика
    tableHeader.querySelectorAll('[data-sort-key]').forEach(th => {
        th.addEventListener('click', () => {
            const sortKey = th.dataset.sortKey;
            sortTable(sortKey);
        });
    });

    tbody.innerHTML = '';
    // ... (остальная часть функции копируется из вашей версии без изменений)
    if (!filteredPlayers?.length) { /* ... */ return; }
    const start = (currentPage - 1) * playersPerPage;
    const end = start + playersPerPage;
    const displayResults = filteredPlayers.slice(start, end);
    displayResults.forEach((result, index) => {
        const change = result.rating_change || 0;
        const changeDisp = change === 0 ? '0' : (change > 0 ? `+${change}` : String(change));
        const changeCls = change > 0 ? 'rating-positive' : (change < 0 ? 'rating-negative' : '');
        let medal = '';
        const place = parseInt(result.place);
        if (place === 1) medal = ' <i class="fas fa-medal text-yellow-400"></i>';
        else if (place === 2) medal = ' <i class="fas fa-medal text-gray-400"></i>';
        else if (place === 3) medal = ' <i class="fas fa-medal text-yellow-600"></i>';
        const row = document.createElement('tr');
        row.className = `cursor-pointer ${index % 2 === 0 ? 'even-row' : 'odd-row'}`;
        row.innerHTML = `<td class="py-3 px-2 text-center">${result.place || '—'}</td><td class="py-3 px-2 text-left">${result.name || '—'}${medal}</td><td class="py-3 px-2 text-center">${result.points || '0'}</td><td class="py-3 px-2 text-center">${result.initial_rating === 0 ? 'б/р' : (result.initial_rating || '—')}</td><td class="py-3 px-2 text-center font-semibold">${result.new_rating === '—' || result.new_rating === 0 ? 'б/р' : (result.new_rating || '0')}</td><td class="py-3 px-2 text-center ${changeCls}">${changeDisp}</td>`;
        row.addEventListener('click', () => {
            if (result.player_id) {
                const pData = players.find(p => p.id == result.player_id);
                if (pData) {
                    updateRightColumnView('PLAYER_CARD', pData);
                } else {
                    updateRightColumnView('DEFAULT');
                }
            } else {
                updateRightColumnView('DEFAULT');
            }
        });
        tbody.appendChild(row);
    });
    updatePagination(start, end);
    toggleRatingFilters(false);
};

    const toggleRatingFilters = (enable) => { 
        RATING_FILTER_BUTTON_IDS.forEach(id => {
            const btn = getElement(id);
            if (btn) { btn.style.pointerEvents = enable ? 'auto' : 'none'; btn.style.opacity = enable ? '1' : '0.5'; btn.classList.toggle('disabled', !enable); }
        });
    };
    
    const updatePagination = (start, end) => { 
        const pagination = getElement('pagination');
        const shownFromEl = getElement('shown-from');
        const shownToEl = getElement('shown-to');
        const totalCountEl = getElement('total-count');
        if (!pagination || !shownFromEl || !shownToEl || !totalCountEl) return;
        pagination.innerHTML = '';
        const pageCount = Math.ceil(filteredPlayers.length / playersPerPage);
        if (pageCount <= 1) {
            shownFromEl.textContent = filteredPlayers.length > 0 ? '1' : '0';
            shownToEl.textContent = filteredPlayers.length.toString();
            totalCountEl.textContent = filteredPlayers.length.toString();
            return;
        }
        const createPageButton = (pageNumber, text, isActive = false, isDisabled = false) => {
            const button = document.createElement('button');
            button.className = `pagination-btn px-3 py-1 rounded-lg ${isActive ? 'active' : ''} ${isDisabled ? 'disabled' : ''}`;
            button.textContent = text || pageNumber.toString();
            button.disabled = isDisabled;
            if (!isDisabled) { button.addEventListener('click', () => { currentPage = pageNumber; if (isTournamentTable) renderTournamentTable(); else renderTable(); }); }
            return button;
        };
        pagination.appendChild(createPageButton(currentPage - 1, 'Предыдущая', false, currentPage === 1));
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(pageCount, currentPage + 2);
        if (currentPage <= 3) endPage = Math.min(pageCount, 5);
        if (currentPage > pageCount - 3) startPage = Math.max(1, pageCount - 4);
        if (startPage > 1) {
            pagination.appendChild(createPageButton(1, '1'));
            if (startPage > 2) { const dots = document.createElement('span'); dots.className = 'px-3 py-1'; dots.textContent = '...'; pagination.appendChild(dots); }
        }
        for (let i = startPage; i <= endPage; i++) pagination.appendChild(createPageButton(i, i.toString(), i === currentPage));
        if (endPage < pageCount) {
            if (endPage < pageCount - 1) { const dots = document.createElement('span'); dots.className = 'px-3 py-1'; dots.textContent = '...'; pagination.appendChild(dots); }
            pagination.appendChild(createPageButton(pageCount, pageCount.toString()));
        }
        pagination.appendChild(createPageButton(currentPage + 1, 'Следующая', false, currentPage === pageCount || pageCount === 0));
        if (filteredPlayers.length === 0) { shownFromEl.textContent = '0'; shownToEl.textContent = '0'; } 
        else { shownFromEl.textContent = (start + 1).toString(); shownToEl.textContent = Math.min(end, filteredPlayers.length).toString(); }
        totalCountEl.textContent = filteredPlayers.length.toString();
    };
    
   // ЗАМЕНИТЕ НА ЭТУ ВЕРСИЮ
const updatePlayerCard = (player) => {
    const set = (id, text) => {
        const element = getElement(id);
        const isRatingField = id.startsWith('player-fshr-') || id.startsWith('player-fide-');
        if (element) element.textContent = (text === null || text === undefined || text === '' || ((text === 0 || text === "0") && isRatingField) ) ? '—' : text;
    };

    const fieldsToClear = ['player-name', 'player-birth-year', 'player-gender', 'player-title', 'player-tournaments', 'player-fshr-id', 'player-fide-id', 'player-fshr-classic', 'player-fshr-rapid', 'player-fshr-blitz', 'player-fide-classic', 'player-fide-rapid', 'player-fide-blitz', 'player-raw-score'];

    if (!player) {
        fieldsToClear.forEach(id => { 
            const el = getElement(id); 
            if(el) el.textContent = id === 'player-name' ? 'Выберите игрока' : '—'; 
        });
        return;
    }

    // --- НОВАЯ ЛОГИКА: Ищем данные игрока в allAchievers ---
    const achieverData = allAchievers.find(a => a.id === player.id);
    const rawScore = achieverData ? achieverData.raw_points : '—';
    set('player-raw-score', rawScore.toString());
    // --- КОНЕЦ НОВОЙ ЛОГИКИ ---

    const name = player.name || '—';
    let formattedName = name;
    const nameParts = name.trim().split(/\s+/);
    if (nameParts.length >= 2) { 
        formattedName = `${nameParts[0]} ${nameParts[1]}`;
        if (nameParts.length > 2) formattedName += `<br>${nameParts.slice(2).join(' ')}`;
    }
    
    const birthYear = player.age && player.age !== '—' ? (new Date().getFullYear()) - parseInt(player.age) : '—';
    const gender = player.gender === 'female' ? 'Ж' : player.gender === 'male' ? 'М' : '—';
    
    const playerNameEl = getElement('player-name');
    if (playerNameEl) playerNameEl.innerHTML = formattedName; 
    
    set('player-birth-year', birthYear.toString()); 
    set('player-gender', gender); 
    set('player-title', player.title);
    set('player-tournaments', player.tournamentsPlayed != null ? player.tournamentsPlayed.toString() : '0');
    set('player-fshr-id', player.id); 
    set('player-fide-id', player.fide_id);
    set('player-fshr-classic', player.rating); 
    set('player-fshr-rapid', player.rapid_rating); 
    set('player-fshr-blitz', player.blitz_rating);
    set('player-fide-classic', player.fide_rating); 
    set('player-fide-rapid', player.fide_rapid); 
    set('player-fide-blitz', player.fide_blitz);
};
    
    const updateFilterInfo = () => { 
        const filterInfo = getElement('filter-info'); if (!filterInfo) return; let mainText = '';
        if (isTournamentTable) mainText = `Участников: ${filteredPlayers.length}`; 
        else if (isSearching) mainText = filteredPlayers.length > 0 ? `Найдено: ${filteredPlayers.length}` : 'Не найдено';
        else if (isWomenFilter) mainText = `Женщин: ${totalFilteredPlayers.length}`;
        else if (isChildrenFilter) mainText = `Детей: ${totalFilteredPlayers.length}`;
        else if (isTop100Filter) mainText = `Топ 100: ${filteredPlayers.length}`; 
        else mainText = `Всего игроков: ${players.length}`;
        filterInfo.textContent = mainText; filterInfo.classList.add('active-info');
        setTimeout(() => filterInfo.classList.remove('active-info'), 500);
    };
    
    const getRatingField = (filterKey) => { 
        const ratingFields = {'fshr-classic':'rating','fshr-rapid':'rapid_rating','fshr-blitz':'blitz_rating','fide-classic':'fide_rating','fide-rapid':'fide_rapid','fide-blitz':'fide_blitz'};
        return ratingFields[filterKey] || 'rating'; 
    };
    
    const applyFilters = () => {
    document.body.classList.remove('tournament-view-active');

    const tournamentSummaryCard = getElement('tournament-summary-card');
    const championsCard = getElement('champions-card');
    const footerContainer = document.querySelector('.footer-container');

    if (tournamentSummaryCard) {
        tournamentSummaryCard.style.display = 'none';
    }
    if (championsCard) {
        championsCard.style.display = '';
    }
    if (footerContainer) {
        footerContainer.style.display = '';
    }

    if (isTournamentTable) { isTournamentTable = false; currentTournamentDetails = null; }

    if (comparisonView && !comparisonView.classList.contains('hidden')) {
        comparisonView.classList.add('hidden');
        tableContainer.classList.remove('hidden');
    }

    updateRightColumnView('DEFAULT');
    playersPerPage = (isTop100Filter && !isTournamentTable) ? 100 : 20;

    let currentFilteredSet = [...players];
    if (isWomenFilter) currentFilteredSet = currentFilteredSet.filter(p => p.gender === 'female');
    if (isChildrenFilter) currentFilteredSet = currentFilteredSet.filter(p => p.isChild === true || p.isChild === 1);

    totalFilteredPlayers = [...currentFilteredSet];

    const searchInputVal = getElement('name-search');
    const searchTerm = searchInputVal ? searchInputVal.value.toLowerCase() : '';
    if (isSearching && searchTerm) {
        currentFilteredSet = currentFilteredSet.filter(p => p.name && p.name.toLowerCase().includes(searchTerm));
    }

    filteredPlayers = [...currentFilteredSet];

    const ratingFieldToSortBy = getRatingField(currentRatingFilter);
    try {
        filteredPlayers.sort((a, b) => {
            const valA = parseInt(a[ratingFieldToSortBy] === '—' ? 0 : a[ratingFieldToSortBy] || '0') || 0;
            const valB = parseInt(b[ratingFieldToSortBy] === '—' ? 0 : b[ratingFieldToSortBy] || '0') || 0;
            if (valA === 0 && valB !== 0) return 1;
            if (valB === 0 && valA !== 0) return -1;
            if (valA === 0 && valB === 0) return (a.name || '').localeCompare(b.name || '', 'ru');
            return valB - valA;
        });
    } catch (error) { console.error('applyFilters: Ошибка сортировки:', error); }

    if (isTop100Filter) filteredPlayers = filteredPlayers.slice(0, 100);

    currentPage = 1;
    renderTable();
    updateFilterInfo();
};
    const handleSearch = () => { 
        if (isTournamentTable) return; 
        const searchInputVal = getElement('name-search'); const searchTerm = searchInputVal ? searchInputVal.value.toLowerCase() : '';
        isSearching = !!searchTerm;
        if (isSearching) { isWomenFilter = false; isChildrenFilter = false; isTop100Filter = false; setActiveMainFilterButton(null); }
        else if(!isWomenFilter && !isChildrenFilter && !isTop100Filter) setActiveMainFilterButton('all-players');
        applyFilters();
    };
    
  const loadTournaments = () => { 
    const tournamentModal = getElement('tournament-modal'); 
    const tournamentSelect = getElement('tournament-select'); 
    const tournamentCancel = getElement('tournament-cancel');
    if (!tournamentSelect || !tournamentModal) return;

    tournamentSelect.innerHTML = '';
    const defaultOption = document.createElement('option');
    defaultOption.value = ""; 
    defaultOption.textContent = "Выберите турнир..."; 
    defaultOption.disabled = true;
    tournamentSelect.appendChild(defaultOption);

    if (tournaments && tournaments.length) {
        tournaments.forEach(tournament => { 
            const option = document.createElement('option'); 
            option.value = tournament.id; 
            option.dataset.tournamentName = tournament.name; 
            option.dataset.tournamentDate = tournament.date; 
            
            // ✅ ИСПРАВЛЕННАЯ СТРОКА: Убрано упоминание переменной ${stars}
            option.textContent = `${tournament.name} (${tournament.date||'Дата не указана'}) [${(tournament.organization||'N/A').toUpperCase()}]`; 
            
            tournamentSelect.appendChild(option); 
        });
        tournamentSelect.size = Math.min(tournaments.length + 1, 15);
        tournamentSelect.focus();
    } else { 
        const noTournamentsOption = document.createElement('option'); 
        noTournamentsOption.value = ""; 
        noTournamentsOption.textContent = "Нет доступных турниров"; 
        noTournamentsOption.disabled = true; 
        tournamentSelect.appendChild(noTournamentsOption); 
        tournamentSelect.size = 2; 
    }

    if (lastSelectedTournamentId) {
        const lastSelectedOption = tournamentSelect.querySelector(`option[value="${lastSelectedTournamentId}"]`);
        if (lastSelectedOption) {
            tournamentSelect.value = lastSelectedTournamentId;
            lastSelectedOption.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    } else {
        tournamentSelect.value = "";
    }

    tournamentSelect.onchange = () => { 
        const selectedOption = tournamentSelect.options[tournamentSelect.selectedIndex]; 
        const tournamentId = parseInt(selectedOption.value); 
        if (tournamentId) { 
            currentTournamentDetails = {id:tournamentId, name:selectedOption.dataset.tournamentName, date:selectedOption.dataset.tournamentDate}; 
            loadTournamentResults(currentTournamentDetails); 
            tournamentModal.classList.add('hidden'); 
            setActiveMainFilterButton('tournaments'); 
        } 
    };
    
    if (tournamentCancel) tournamentCancel.onclick = () => tournamentModal.classList.add('hidden');
    tournamentModal.onclick = (e) => { if (e.target === tournamentModal) tournamentModal.classList.add('hidden'); };
};
    
   const loadTournamentResults = (tournamentDetailsInput) => {
    console.log(`%c[LOAD_TOURNAMENT] Начало загрузки турнира ID: ${tournamentDetailsInput.id}`, 'color: green; font-weight: bold;');
    lastSelectedTournamentId = tournamentDetailsInput.id;
    document.body.classList.add('tournament-view-active');
    playersPerPage = 100;
    showLoader();

    fetch(`/api/tournament/${tournamentDetailsInput.id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('[LOAD_TOURNAMENT] Данные с сервера:', data);

            if (data.error) {
                console.error("[LOAD_TOURNAMENT] Ошибка от API:", data.error);
                const tbody = getElement('players-table');
                if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="py-3 px-4 text-center text-red-500">Не удалось загрузить.</td></tr>`;
                updateRightColumnView('DEFAULT');
                return;
            }

            currentTournamentDetails = {
                id: tournamentDetailsInput.id,
                name: data.name || tournamentDetailsInput.name,
                date: data.date || tournamentDetailsInput.date,
                highlights: data.highlights || null,
                tier: data.tier
            };

            filteredPlayers = data.results || [];

            if (filteredPlayers.length > 0 && filteredPlayers[0].place) {
                try {
                    filteredPlayers.sort((a, b) => (parseInt(String(a.place).split('-')[0] || '9999') - parseInt(String(b.place).split('-')[0] || '9999')));
                } catch (e) {
                    console.error("Ошибка сортировки результатов турнира:", e);
                }
            }

            currentPage = 1;
            isTournamentTable = true;
            
            console.log('[LOAD_TOURNAMENT] Вызов renderTournamentTable()');
            renderTournamentTable();
            
            console.log('%c[LOAD_TOURNAMENT] Вызов updateRightColumnView для саммари', 'color: red; font-weight: bold;');
            // Этот блок полностью заменяет предыдущий
if (currentTournamentDetails.highlights) {
    console.log('[LOAD_TOURNAMENT] Данные highlights:', currentTournamentDetails.highlights);
    updateRightColumnView('TOURNAMENT_SUMMARY', { 
        highlights: currentTournamentDetails.highlights,
        results: filteredPlayers 
    });
} else {
    console.warn('[LOAD_TOURNAMENT] Отсутствуют данные highlights для саммари.');
    // Убедимся, что карточка саммари пуста, если данных нет
    const contentEl = getElement('tournament-summary-content');
    if (contentEl) {
        contentEl.innerHTML = '<p class="text-center">Дополнительная статистика по турниру недоступна.</p>';
    }
    // Больше ничего не делаем. CSS сам разберется, что показывать и скрывать.
}
            
            console.log('[LOAD_TOURNAMENT] Вызов updateFilterInfo()');
            updateFilterInfo();
            forceTournamentViewLayout();
            console.log('%c[LOAD_TOURNAMENT] Завершено', 'color: green; font-weight: bold;');
        })
        .catch(error => {
            console.error('[LOAD_TOURNAMENT] Ошибка в fetch:', error);
            const tbody = getElement('players-table');
            if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="py-3 px-4 text-center text-red-500">Не удалось загрузить.</td></tr>`;
            updateRightColumnView('DEFAULT');
        });
};
    window.sortTable = (columnKey) => { 
        const tableHeaderElem = getElement('table-header'); if (!tableHeaderElem) return; let thElementsParent; const headerRows = tableHeaderElem.querySelectorAll('tr');
        if (isTournamentTable) thElementsParent = headerRows.length > 1 && headerRows[0].querySelector('th[colspan]') ? headerRows[1] : headerRows[0];
        else thElementsParent = headerRows.length > 1 ? headerRows[1] : headerRows[0];
        if (!thElementsParent) return;
        thElementsParent.querySelectorAll('th[onclick]').forEach(th => { if(th.getAttribute('onclick').includes(columnKey)) return; th.classList.remove('sort-asc', 'sort-desc'); const icon = th.querySelector('.sort-icon'); if (icon) icon.remove(); });
        sortDirection[columnKey] = (sortDirection[columnKey] === 'asc') ? 'desc' : 'asc';
        Object.keys(sortDirection).forEach(key => { if (key !== columnKey) delete sortDirection[key]; });
        const direction = sortDirection[columnKey] === 'asc' ? 1 : -1;
        const thElement = Array.from(thElementsParent.querySelectorAll('th[onclick]')).find(th => th.getAttribute('onclick')?.includes(`sortTable('${columnKey}')`));
        if (thElement) { const oldIcon = thElement.querySelector('.sort-icon'); if (oldIcon) oldIcon.remove(); thElement.classList.remove('sort-asc', 'sort-desc'); thElement.classList.add(direction === 1 ? 'sort-asc' : 'sort-desc'); const sortIcon = document.createElement('i'); sortIcon.className = `fas ${direction === 1 ? 'fa-sort-up' : 'fa-sort-down'} ml-1 sort-icon`; thElement.appendChild(sortIcon); }
        if (!filteredPlayers || !Array.isArray(filteredPlayers)) return;
        filteredPlayers.sort((a, b) => {
            let valA, valB;
            if (isTournamentTable) { 
                switch (columnKey) {
                    case 'name': valA=(a.name||'').toLowerCase(); valB=(b.name||'').toLowerCase(); break;
                    case 'place': valA=parseInt(String(a.place).split('-')[0]||'9999'); valB=parseInt(String(b.place).split('-')[0]||'9999'); break;
                    case 'points': valA=parseFloat(a.points)||0; valB=parseFloat(b.points)||0; break;
                    case 'initial_rating': valA=parseInt(a.initial_rating==='б/р'?0:a.initial_rating)||0; valB=parseInt(b.initial_rating==='б/р'?0:b.initial_rating)||0; break;
                    case 'new_rating': valA=(a.new_rating==='—'||a.new_rating==='б/р'||a.new_rating===0?-1:parseInt(a.new_rating))||-1; valB=(b.new_rating==='—'||b.new_rating==='б/р'||b.new_rating===0?-1:parseInt(b.new_rating))||-1; break;
                    case 'rating_change': valA=parseInt(a.rating_change)||0; valB=parseInt(b.rating_change)||0; break; 
                    default: return 0;
                }
            } else { 
                switch (columnKey) {
                    case 'name': valA=(a.name||'').toLowerCase(); valB=(b.name||'').toLowerCase(); break;
                    case 'title': valA=(a.title||'').toLowerCase(); valB=(b.title||'').toLowerCase(); break;
                    case 'rating': const rf=getRatingField(currentRatingFilter); valA=parseInt(a[rf]==='—'?0:a[rf]||'0')||0; valB=parseInt(b[rf]==='—'?0:b[rf]||'0')||0; break;
                    case 'change': if(currentRatingFilter.startsWith('fshr-')){ if(currentRatingFilter==='fshr-classic'){valA=a.change_classic_value||0;valB=b.change_classic_value||0;} else if(currentRatingFilter==='fshr-rapid'){valA=a.change_rapid_value||0;valB=b.change_rapid_value||0;} else if(currentRatingFilter==='fshr-blitz'){valA=a.change_blitz_value||0;valB=b.change_blitz_value||0;} else{valA=0;valB=0;} }else{valA=0;valB=0;} break;
                    case 'age': valA=(a.age==='—'?999:parseInt(a.age))||999; valB=(b.age==='—'?999:parseInt(b.age))||999; break; 
                    default: return 0;
                }
            }
            if(valA===undefined||valB===undefined)return 0;
            if(typeof valA==='string')return direction*valA.localeCompare(valB,'ru',{sensitivity:'base'});
            if(typeof valA==='number'){
                if(columnKey==='rating'||columnKey==='initial_rating'||columnKey==='new_rating'){ if(valA===-1&&valB!==-1)return direction*1;if(valB===-1&&valA!==-1)return direction*-1; if(valA===-1&&valB===-1)return 0;if(valA===0&&valB!==0)return direction*1; if(valB===0&&valA!==0)return direction*-1; }
                return direction*(valA-valB);
            } return direction*(String(valA).localeCompare(String(valB),'ru',{sensitivity:'base'}));
        });
        currentPage = 1; if (isTournamentTable) renderTournamentTable(); else renderTable();
    };
    
    // ✅ НАЧАЛО: НОВЫЕ ФУНКЦИИ ДЛЯ СРАВНЕНИЯ
    
    /**
     * Запускает процесс сравнения после выбора второго игрока
     * @param {object} playerB - Объект второго игрока
     */
    function startComparison(playerB) {
        comparisonModal.classList.add('hidden');
        tableContainer.classList.add('hidden'); // Скрываем основную таблицу
        if(comparisonView) {
            comparisonView.classList.remove('hidden');
            comparisonView.innerHTML = '<div class="text-center p-8 rounded-lg shadow-lg">Загрузка данных для сравнения...</div>';
        }

        fetch(`/api/compare?player1_id=${playerAForComparison.id}&player2_id=${playerB.id}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    if(comparisonView) comparisonView.innerHTML = `<div class="text-center p-8 text-red-500 rounded-lg shadow-lg">Ошибка: ${data.error}</div>`;
                } else {
                    renderComparisonView(data);
                }
            })
            .catch(err => {
                console.error("Ошибка при сравнении игроков:", err);
                if(comparisonView) comparisonView.innerHTML = `<div class="text-center p-8 text-red-500 rounded-lg shadow-lg">Не удалось загрузить данные.</div>`;
            });
    }

    /**
     * "Рисует" таблицу сравнения
     * @param {object} data - Данные для сравнения от API
     */
  // ✅ НАЧАЛО: ФИНАЛЬНАЯ ВЕРСИЯ ФУНКЦИИ С КЛАССИЧЕСКИМ СТИЛЕМ
// ================================================================
// НАЧНИТЕ ВЫДЕЛЯТЬ ОТСЮДА
// ================================================================

function renderComparisonView(data) {
    const { player1, player2, head_to_head, prizes_player1, prizes_player2 } = data;

    const createInfoCardHTML = (player) => {
    const birthYear = player.age && player.age !== '—' ? (new Date().getFullYear()) - parseInt(player.age) : '—';
    
    const nameParts = player.name.split(' ');
    const shortName = nameParts.length > 2 ? `${nameParts[0]} ${nameParts[1]}` : player.name;

    return `
        <div class="report-info-card">
            <h3 style="text-align: center;">${shortName}</h3>
            <p><span>Год рождения:</span> <span>${birthYear}</span></p>
            <p><span>Звание:</span> <span>${player.title || '—'}</span></p>
            <p class="font-semibold border-t pt-2 mt-2"><span>Сумма очков:</span> <span>${player.raw_points || '—'}</span></p>
            <p><span>Классика:</span> <span>${player.rating || '—'}</span></p>
            <p><span>Рапид:</span> <span>${player.rapid_rating || '—'}</span></p>
            <p><span>Блиц:</span> <span>${player.blitz_rating || '—'}</span></p>
            <div class="text-center mt-4">
                <button 
                    class="compare-button-styled re-compare-btn" 
                    data-player-id="${player.id}">
                    <i class="fa-solid fa-bolt"></i>
                    <span>Сравнить</span>
                </button>
            </div>
        </div>`;
};

    const createComparisonTablesHTML = () => {
        const getRow = (label, val1, val2) => {
            const num1 = parseInt(val1) || 0;
            const num2 = parseInt(val2) || 0;
            let class1 = '', class2 = '';
            if (label !== 'Возраст') {
                if (num1 > num2) { class1 = 'stat-better'; } 
                else if (num2 > num1) { class2 = 'stat-better'; }
            }
            return `<tr><td class="${class1}">${val1}</td><th class="font-normal text-sm">${label}</th><td class="${class2}">${val2}</td></tr>`;
        };
        const { player1_wins, player2_wins, draws } = head_to_head;
        let p1_score_class = '', p2_score_class = '';
        if (player1_wins > player2_wins) { p1_score_class = 'stat-better'; p2_score_class = 'stat-worse'; }
        else if (player2_wins > player1_wins) { p2_score_class = 'stat-better'; p1_score_class = 'stat-worse'; }

        return `
            <div class="report-block">
                <h3>Личные встречи</h3>
                <div class="h2h-section">
                    <div class="h2h-score"><span class="${p1_score_class}">${player1_wins}</span><span> – </span><span class="${p2_score_class}">${player2_wins}</span></div>
                    <div class="h2h-draws">Ничьи: ${draws}</div>
                </div>
            </div>
            <div class="report-block">
                <h3>Статистика и достижения</h3>
                <table class="center-stats-table">
                    <tbody>
                        ${getRow('Возраст', player1.age, player2.age)}
                        ${getRow('Сыграно турниров', player1.tournamentsPlayed, player2.tournamentsPlayed)}
                        <tr class="border-t"><td colspan="3" class="pt-4"></td></tr>
                        ${getRow('🥇 Золото', prizes_player1.gold, prizes_player2.gold)}
                        ${getRow('🥈 Серебро', prizes_player1.silver, prizes_player2.silver)}
                        ${getRow('🥉 Бронза', prizes_player1.bronze, prizes_player2.bronze)}
                    </tbody>
                </table>
            </div>
        `;
    };

    const createFinalScoreHTML = () => {
        let p1_ovr_class = '', p2_ovr_class = '';
        if (player1.overall_rating > player2.overall_rating) {
            p1_ovr_class = 'stat-better'; p2_ovr_class = 'stat-worse';
        } else if (player2.overall_rating > player1.overall_rating) {
            p2_ovr_class = 'stat-better'; p1_ovr_class = 'stat-worse';
        }
        return `
            <div class="report-block">
                <h3 class="text-xl font-bold">Итоговая сила</h3>
                <div class="final-score-container">
                    <div class="final-score-value ${p1_ovr_class}">${player1.overall_rating}</div>
                    <div class="final-score-dash">–</div>
                    <div class="final-score-value ${p2_ovr_class}">${player2.overall_rating}</div>
                </div>
            </div>`;
    };

    const comparisonHTML = `
        <div class="w-full">
            <div class="flex justify-end mb-4">
                <button id="close-comparison-btn" class="px-4 py-2 rounded">Закрыть</button>
            </div>
            <div class="comparison-report">
                <div class="report-row-presentation">
                    ${createInfoCardHTML(player1)}
                    <div class="presentation-vs">VS</div>
                    ${createInfoCardHTML(player2)}
                </div>
                ${createComparisonTablesHTML()}
                ${createFinalScoreHTML()}
            </div>
        </div>
    `;

    if (comparisonView) comparisonView.innerHTML = comparisonHTML;

    // --- ДОБАВЛЕН ОБРАБОТЧИК СОБЫТИЙ ДЛЯ НОВЫХ КНОПОК ---
    if (comparisonView) {
        comparisonView.addEventListener('click', (event) => {
            const button = event.target.closest('.re-compare-btn');
            if (button) {
                const playerId = button.dataset.playerId;
                const selectedPlayer = players.find(p => p.id === playerId);
                if (selectedPlayer) {
                    playerAForComparison = selectedPlayer;
                    
                    // Открываем модальное окно для выбора второго игрока
                    if (comparisonModal) comparisonModal.classList.remove('hidden');
                    if (comparisonSearchInput) {
                        comparisonSearchInput.value = '';
                        comparisonSearchInput.focus();
                    }
                    if (comparisonSearchResults) comparisonSearchResults.innerHTML = '';
                }
            }
            
            // Обработка кнопки "Закрыть"
            if (event.target.closest('#close-comparison-btn')) {
                if (comparisonView) {
                    comparisonView.classList.add('hidden');
                    comparisonView.innerHTML = '';
                }
                if (tableContainer) tableContainer.classList.remove('hidden');
            }
        });
    }
}

// КОНЕЦ: ФИНАЛЬНАЯ ВЕРСИЯ ФУНКЦИИ ОТРИСОВКИ
    // КОНЕЦ: НОВЫЕ ФУНКЦИИ ДЛЯ СРАВНЕНИЯ

    const bindRatingFilterEvents=()=>RATING_FILTER_BUTTON_IDS.forEach(id=>getElement(id)?.addEventListener('click',handleFilterClick));
    function handleFilterClick(event){try{const btn=event.currentTarget;if(btn.classList.contains('disabled'))return;const filter=btn.id.replace('filter-','');RATING_FILTER_BUTTON_IDS.forEach(id=>getElement(id)?.classList.remove('active'));btn.classList.add('active');currentRatingFilter=filter;if(!isTournamentTable)applyFilters();}catch(error){console.error('Ошибка в handleFilterClick:',error);}}
    bindRatingFilterEvents(); 
    const setActiveMainFilterButton=(activeButtonId)=>['all-players','women','children','top100','tournaments'].forEach(id=>getElement(id)?.classList.toggle('active',id===activeButtonId));
    
    getElement('all-players')?.addEventListener('click',()=>{isTop100Filter=false;isWomenFilter=false;isChildrenFilter=false;isSearching=false;getElement('name-search').value='';isTournamentTable=false;currentTournamentDetails=null;setActiveMainFilterButton('all-players');updateRightColumnView('DEFAULT');applyFilters();});
    getElement('women')?.addEventListener('click',()=>{isWomenFilter=!isWomenFilter;isChildrenFilter=false;isTop100Filter=false;isSearching=false;getElement('name-search').value='';isTournamentTable=false;currentTournamentDetails=null;setActiveMainFilterButton(isWomenFilter?'women':'all-players');updateRightColumnView('DEFAULT');applyFilters();});
    getElement('children')?.addEventListener('click',()=>{isChildrenFilter=!isChildrenFilter;isWomenFilter=false;isTop100Filter=false;isSearching=false;getElement('name-search').value='';isTournamentTable=false;currentTournamentDetails=null;setActiveMainFilterButton(isChildrenFilter?'children':'all-players');updateRightColumnView('DEFAULT');applyFilters();});
    getElement('top100')?.addEventListener('click',()=>{isTop100Filter=!isTop100Filter;isWomenFilter=false;isChildrenFilter=false;isSearching=false;getElement('name-search').value='';isTournamentTable=false;currentTournamentDetails=null;setActiveMainFilterButton(isTop100Filter?'top100':'all-players');updateRightColumnView('DEFAULT');applyFilters();});
    getElement('tournaments')?.addEventListener('click',()=>{const tModal=getElement('tournament-modal');if(tModal){tModal.classList.remove('hidden');loadTournaments();}});
    
    getElement('name-search')?.addEventListener('input',handleSearch);
    document.querySelector('.search-container i.bi-search')?.addEventListener('click',()=>{handleSearch();getElement('name-search')?.focus();});
    
    document.querySelectorAll('.theme-btn').forEach(btn=>btn.addEventListener('click',()=>applyTheme(btn.dataset.theme)));

    // ✅ НАЧАЛО: НОВЫЕ ОБРАБОТЧИКИ ДЛЯ СРАВНЕНИЯ

    // Открывает модальное окно для выбора второго игрока
    if (compareBtn) {
        compareBtn.addEventListener('click', () => {
            const selectedPlayerId = getElement('player-fshr-id')?.textContent;
            if (selectedPlayerId) {
                playerAForComparison = players.find(p => p.id === selectedPlayerId);
            }
            if (playerAForComparison) {
                 console.log('Попытка очистить поле. Содержимое переменной comparisonSearchInput:', comparisonSearchInput);
                if(comparisonModal) comparisonModal.classList.remove('hidden');
                if(comparisonSearchInput) {
                    comparisonSearchInput.value = '';
                    comparisonSearchInput.focus();
                }
                if(comparisonSearchResults) comparisonSearchResults.innerHTML = '';
            }
        });
    }

    // Закрывает модальное окно
    if (comparisonCancelBtn) {
        comparisonCancelBtn.addEventListener('click', () => {
            if(comparisonModal) comparisonModal.classList.add('hidden');
        });
    }
    if (comparisonModal) {
        comparisonModal.addEventListener('click', (e) => {
            if (e.target === comparisonModal) {
                comparisonModal.classList.add('hidden');
            }
        });
    }

    // Поиск в модальном окне
    if (comparisonSearchInput) {
        comparisonSearchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            if (!comparisonSearchResults) return;

            if (searchTerm.length < 2) {
                comparisonSearchResults.innerHTML = '';
                return;
            }
            const results = players.filter(p => 
                p.id !== playerAForComparison?.id && p.name.toLowerCase().includes(searchTerm)
            );
            
            comparisonSearchResults.innerHTML = '';
            if (results.length > 0) {
                results.slice(0, 10).forEach(player => {
                    const li = document.createElement('li');
                    li.className = 'p-2 hover:bg-gray-200 cursor-pointer text-black';
                    li.textContent = `${player.name} (${player.rating})`;
                    li.dataset.playerId = player.id;
                    li.addEventListener('click', () => startComparison(player));
                    comparisonSearchResults.appendChild(li);
                });
            } else {
                comparisonSearchResults.innerHTML = '<li class="p-2 text-gray-500">Игроки не найдены</li>';
            }
        });
    }
    getElement('show-history-btn')?.addEventListener('click', displayChampionHistory);
});
