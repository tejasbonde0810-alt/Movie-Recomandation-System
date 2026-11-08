/**
 * Global Movie & Web Series Recommendation Engine
 * Minimalist Vanilla JavaScript Frontend Controller
 */

(function () {
    'use strict';

    // Application State
    const state = {
        engine: 'movie', // 'movie' or 'tv'
        metadata: {
            languages: [],
            movie_genres: [],
            tv_genres: [],
            has_token: false,
            cache_stats: { cached_api_responses: 0, cached_titles: 0 }
        },
        activeSearchQuery: '',
        activeRecommendationTarget: null
    };

    // DOM Elements
    const elements = {
        navMovies: document.getElementById('navMovies'),
        navTv: document.getElementById('navTv'),
        engineLabel: document.getElementById('engineLabel'),
        cacheLabel: document.getElementById('cacheLabel'),
        btnSyncCache: document.getElementById('btnSyncCache'),
        systemStatus: document.getElementById('systemStatus'),
        
        searchForm: document.getElementById('searchForm'),
        searchInput: document.getElementById('searchInput'),
        btnClearSearch: document.getElementById('btnClearSearch'),
        
        filterFeed: document.getElementById('filterFeed'),
        filterLanguage: document.getElementById('filterLanguage'),
        filterGenre: document.getElementById('filterGenre'),
        filterYear: document.getElementById('filterYear'),
        btnApplyFilters: document.getElementById('btnApplyFilters'),

        alertBox: document.getElementById('alertBox'),
        alertMessage: document.getElementById('alertMessage'),
        alertClose: document.getElementById('alertClose'),

        recommendationContext: document.getElementById('recommendationContext'),
        targetTitle: document.getElementById('targetTitle'),
        targetMeta: document.getElementById('targetMeta'),
        btnClearContext: document.getElementById('btnClearContext'),

        resultsHeading: document.getElementById('resultsHeading'),
        resultsCount: document.getElementById('resultsCount'),
        resultsList: document.getElementById('resultsList'),
        loadingIndicator: document.getElementById('loadingIndicator'),
        loadingText: document.getElementById('loadingText'),
        emptyState: document.getElementById('emptyState')
    };

    // =========================================================================
    // Initialization & Metadata Loading
    // =========================================================================
    async function init() {
        populateYearDropdown();
        bindEvents();
        await loadMetadata();
        updateEngineUI();
        loadFeed();
    }

    function populateYearDropdown() {
        const currentYear = new Date().getFullYear();
        const select = elements.filterYear;
        select.innerHTML = '<option value="">All Years</option>';
        for (let y = currentYear; y >= 1960; y--) {
            const opt = document.createElement('option');
            opt.value = y.toString();
            opt.textContent = y.toString();
            select.appendChild(opt);
        }
    }

    async function loadMetadata() {
        try {
            const res = await fetch('/api/config/meta');
            const data = await res.json();
            if (data.status === 'success') {
                state.metadata = data;
                updateGenreDropdown();
                updateSystemStatus(data.has_token);
                updateCacheStats(data.cache_stats);
            }
        } catch (err) {
            console.error('Failed to load system metadata:', err);
            showAlert('Could not load server configuration.', 'error');
        }
    }

    function updateSystemStatus(hasToken) {
        if (hasToken) {
            elements.systemStatus.textContent = 'Live TMDB API Connected';
            elements.systemStatus.className = 'status-pill status-ready';
        } else {
            elements.systemStatus.textContent = 'Demo Mode (Offline Mock Data)';
            elements.systemStatus.className = 'status-pill status-warning';
            showAlert('TMDB Bearer token not set in .env. Running in offline demo mode with curated titles.', 'info');
        }
    }

    function updateCacheStats(stats) {
        if (!stats) return;
        const total = (stats.cached_api_responses || 0) + (stats.cached_titles || 0);
        elements.cacheLabel.textContent = `${total} items in local store`;
    }

    function updateGenreDropdown() {
        const select = elements.filterGenre;
        const genres = state.engine === 'movie' ? state.metadata.movie_genres : state.metadata.tv_genres;
        select.innerHTML = '<option value="">All Genres</option>';
        if (genres && genres.length > 0) {
            genres.forEach(g => {
                const opt = document.createElement('option');
                opt.value = g.name;
                opt.textContent = g.name;
                select.appendChild(opt);
            });
        }
    }

    // =========================================================================
    // Event Listeners
    // =========================================================================
    function bindEvents() {
        // Navigation Switch
        elements.navMovies.addEventListener('click', () => switchEngine('movie'));
        elements.navTv.addEventListener('click', () => switchEngine('tv'));

        // Search
        elements.searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = elements.searchInput.value.trim();
            if (query) {
                clearRecommendationContext();
                state.activeSearchQuery = query;
                executeSearch(query);
            }
        });

        elements.btnClearSearch.addEventListener('click', () => {
            elements.searchInput.value = '';
            state.activeSearchQuery = '';
            clearRecommendationContext();
            loadFeed();
        });

        // Feed & Filter Controls
        elements.filterFeed.addEventListener('change', () => {
            elements.searchInput.value = '';
            state.activeSearchQuery = '';
            clearRecommendationContext();
            loadFeed();
        });

        elements.btnApplyFilters.addEventListener('click', () => {
            clearRecommendationContext();
            if (state.activeSearchQuery) {
                executeSearch(state.activeSearchQuery);
            } else {
                loadDiscover();
            }
        });

        // Recommendation Context Clear
        elements.btnClearContext.addEventListener('click', () => {
            clearRecommendationContext();
            loadFeed();
        });

        // Alert close
        elements.alertClose.addEventListener('click', () => {
            elements.alertBox.classList.add('hidden');
        });

        // Cache Sync
        elements.btnSyncCache.addEventListener('click', async () => {
            elements.btnSyncCache.disabled = true;
            elements.btnSyncCache.textContent = 'Syncing...';
            try {
                const res = await fetch('/api/sync', { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success') {
                    showAlert(data.message, 'info');
                    await loadMetadata();
                } else {
                    showAlert(data.message || 'Sync failed.', 'error');
                }
            } catch (err) {
                showAlert('Failed to contact sync service.', 'error');
            } finally {
                elements.btnSyncCache.disabled = false;
                elements.btnSyncCache.textContent = 'Sync Top Titles';
            }
        });
    }

    // =========================================================================
    // Engine Switching
    // =========================================================================
    function switchEngine(newEngine) {
        if (state.engine === newEngine) return;
        state.engine = newEngine;
        clearRecommendationContext();
        elements.searchInput.value = '';
        state.activeSearchQuery = '';

        updateEngineUI();
        updateGenreDropdown();
        loadFeed();
    }

    function updateEngineUI() {
        if (state.engine === 'movie') {
            elements.navMovies.classList.add('active');
            elements.navTv.classList.remove('active');
            elements.engineLabel.textContent = 'Movie Engine';
            elements.searchInput.placeholder = 'Search movie title (e.g. Inception, 3 Idiots, RRR, Parasite)...';
        } else {
            elements.navTv.classList.add('active');
            elements.navMovies.classList.remove('active');
            elements.engineLabel.textContent = 'Web Series Engine';
            elements.searchInput.placeholder = 'Search TV series title (e.g. Breaking Bad, Sacred Games, Squid Game)...';
        }
    }

    // =========================================================================
    // Data Loading & API Calls
    // =========================================================================
    async function loadFeed() {
        const feedMode = elements.filterFeed.value;
        const lang = elements.filterLanguage.value;
        const genre = elements.filterGenre.value;
        const year = elements.filterYear.value;

        // If specific filters are applied, route to discover
        if (lang || genre || year || feedMode === 'custom') {
            loadDiscover();
            return;
        }

        showLoading(true, `Loading ${feedMode} ${state.engine === 'movie' ? 'movies' : 'series'}...`);

        try {
            let endpoint = '';
            let headingText = '';

            if (state.engine === 'movie') {
                if (feedMode === 'trending') {
                    endpoint = '/api/movies/trending';
                    headingText = 'Trending Movies';
                } else if (feedMode === 'popular') {
                    endpoint = '/api/movies/discover?sort_by=popularity.desc';
                    headingText = 'Popular Movies';
                } else if (feedMode === 'top_rated') {
                    endpoint = '/api/movies/discover?sort_by=vote_average.desc';
                    headingText = 'Top Rated Movies';
                } else if (feedMode === 'recent') {
                    endpoint = '/api/movies/discover?sort_by=primary_release_date.desc';
                    headingText = 'Recently Released Movies';
                }
            } else {
                if (feedMode === 'trending') {
                    endpoint = '/api/tv/trending';
                    headingText = 'Trending TV & Web Series';
                } else if (feedMode === 'popular') {
                    endpoint = '/api/tv/discover?sort_by=popularity.desc';
                    headingText = 'Popular TV & Web Series';
                } else if (feedMode === 'top_rated') {
                    endpoint = '/api/tv/discover?sort_by=vote_average.desc';
                    headingText = 'Top Rated TV & Web Series';
                } else if (feedMode === 'recent') {
                    endpoint = '/api/tv/discover?sort_by=first_air_date.desc';
                    headingText = 'Recently Released TV & Web Series';
                }
            }

            const res = await fetch(endpoint);
            const json = await res.json();

            if (json.status === 'success' && json.data) {
                renderResults(json.data.results || [], headingText);
            } else {
                showAlert(json.message || 'Failed to fetch items.', 'error');
                renderResults([], headingText);
            }
        } catch (err) {
            showAlert('Network error while fetching feed.', 'error');
            renderResults([], 'Feed');
        } finally {
            showLoading(false);
        }
    }

    async function loadDiscover() {
        const lang = elements.filterLanguage.value;
        const genre = elements.filterGenre.value;
        const year = elements.filterYear.value;
        const feedMode = elements.filterFeed.value;

        let sortBy = 'popularity.desc';
        if (feedMode === 'top_rated') sortBy = 'vote_average.desc';
        if (feedMode === 'recent') sortBy = state.engine === 'movie' ? 'primary_release_date.desc' : 'first_air_date.desc';

        const params = new URLSearchParams();
        if (lang) params.append('language', lang);
        if (genre) params.append('genre', genre);
        if (year) params.append('year', year);
        params.append('sort_by', sortBy);

        const baseUrl = state.engine === 'movie' ? '/api/movies/discover' : '/api/tv/discover';
        const url = `${baseUrl}?${params.toString()}`;

        showLoading(true, `Discovering ${state.engine === 'movie' ? 'movies' : 'series'}...`);

        try {
            const res = await fetch(url);
            const json = await res.json();
            if (json.status === 'success' && json.data) {
                const label = state.engine === 'movie' ? 'Movies' : 'Web Series';
                const filterDesc = lang ? ` [Language: ${lang.toUpperCase()}]` : '';
                renderResults(json.data.results || [], `Discovered ${label}${filterDesc}`);
            } else {
                showAlert(json.message || 'Discovery returned no results.', 'error');
                renderResults([], 'Discovery Results');
            }
        } catch (err) {
            showAlert('Failed to discover titles.', 'error');
            renderResults([], 'Discovery Results');
        } finally {
            showLoading(false);
        }
    }

    async function executeSearch(query) {
        showLoading(true, `Searching for "${query}"...`);
        const lang = elements.filterLanguage.value;
        const genre = elements.filterGenre.value;
        const year = elements.filterYear.value;

        const params = new URLSearchParams({ q: query });
        if (lang) params.append('language', lang);
        if (genre) params.append('genre', genre);
        if (year) params.append('year', year);

        const baseUrl = state.engine === 'movie' ? '/api/movies/search' : '/api/tv/search';
        const url = `${baseUrl}?${params.toString()}`;

        try {
            const res = await fetch(url);
            const json = await res.json();
            if (json.status === 'success' && json.data) {
                renderResults(json.data.results || [], `Search Results for "${query}"`);
            } else {
                showAlert(json.message || 'Search failed.', 'error');
                renderResults([], `Search Results for "${query}"`);
            }
        } catch (err) {
            showAlert('Network error during search.', 'error');
            renderResults([], 'Search Results');
        } finally {
            showLoading(false);
        }
    }

    async function requestRecommendations(itemId, itemTitle, itemYear, itemMedia) {
        showLoading(true, `Calculating content-based recommendations for "${itemTitle}"...`);
        const endpoint = itemMedia === 'tv'
            ? `/api/tv/${itemId}/recommendations`
            : `/api/movies/${itemId}/recommendations`;

        try {
            const res = await fetch(endpoint);
            const json = await res.json();

            if (json.status === 'success' && json.data) {
                const data = json.data;
                const recs = data.recommendations || [];
                
                // Show recommendation banner
                showRecommendationContext(itemTitle, itemYear, itemMedia, recs.length);

                renderResults(
                    recs,
                    `Recommendations for: ${itemTitle}`,
                    true // isRecommendationMode
                );
            } else {
                showAlert(json.message || 'Could not generate recommendations for this title.', 'error');
            }
        } catch (err) {
            showAlert('Error requesting recommendations.', 'error');
        } finally {
            showLoading(false);
        }
    }

    // =========================================================================
    // UI Rendering
    // =========================================================================
    function renderResults(items, heading, isRecommendationMode = false) {
        elements.resultsHeading.textContent = heading;
        elements.resultsCount.textContent = `${items.length} item${items.length === 1 ? '' : 's'}`;
        elements.resultsList.innerHTML = '';

        if (!items || items.length === 0) {
            elements.emptyState.classList.remove('hidden');
            return;
        }

        elements.emptyState.classList.add('hidden');

        items.forEach(item => {
            const row = document.createElement('div');
            row.className = 'result-row';

            // Top bar: Title, Year, Badges
            const topDiv = document.createElement('div');
            topDiv.className = 'row-top';

            const titleWrap = document.createElement('div');
            titleWrap.className = 'title-meta-wrap';

            const titleSpan = document.createElement('span');
            titleSpan.className = 'row-title';
            titleSpan.textContent = item.title || 'Untitled';

            const yearSpan = document.createElement('span');
            yearSpan.className = 'row-year';
            yearSpan.textContent = `(${item.release_year || 'N/A'})`;

            titleWrap.appendChild(titleSpan);
            titleWrap.appendChild(yearSpan);

            const badgeGroup = document.createElement('div');
            badgeGroup.className = 'badge-group';

            // Similarity Score badge (if recommended)
            if (item.similarity_percent !== undefined) {
                const scoreBadge = document.createElement('span');
                scoreBadge.className = 'badge badge-score';
                scoreBadge.textContent = `${item.similarity_percent}% Match`;
                badgeGroup.appendChild(scoreBadge);
            }

            // Language Badge
            const langBadge = document.createElement('span');
            langBadge.className = 'badge badge-lang';
            langBadge.textContent = item.original_language ? item.original_language.toUpperCase() : 'EN';
            badgeGroup.appendChild(langBadge);

            // Rating Badge
            const ratingBadge = document.createElement('span');
            ratingBadge.className = 'badge badge-rating';
            ratingBadge.textContent = `★ ${item.vote_average ? item.vote_average.toFixed(1) : '0.0'}`;
            badgeGroup.appendChild(ratingBadge);

            // Genre Badges
            if (item.genres && Array.isArray(item.genres)) {
                item.genres.slice(0, 3).forEach(g => {
                    const gb = document.createElement('span');
                    gb.className = 'badge badge-genre';
                    gb.textContent = g;
                    badgeGroup.appendChild(gb);
                });
            }

            topDiv.appendChild(titleWrap);
            topDiv.appendChild(badgeGroup);
            row.appendChild(topDiv);

            // Overview
            const overviewP = document.createElement('p');
            overviewP.className = 'row-overview';
            overviewP.textContent = item.overview || 'No overview available.';
            row.appendChild(overviewP);

            // Director / Cast / Country subline if present
            if (item.director || (item.cast && item.cast.length > 0) || item.production_country_string) {
                const crewDiv = document.createElement('div');
                crewDiv.className = 'row-crew';
                const parts = [];
                if (item.director) {
                    const label = state.engine === 'movie' ? 'Director' : 'Creator';
                    parts.push(`<strong>${label}:</strong> ${escapeHtml(item.director)}`);
                }
                if (item.cast && item.cast.length > 0) {
                    parts.push(`<strong>Cast:</strong> ${escapeHtml(item.cast.slice(0, 3).join(', '))}`);
                }
                if (item.production_country_string) {
                    parts.push(`<strong>Origin:</strong> ${escapeHtml(item.production_country_string)}`);
                }
                crewDiv.innerHTML = parts.join(' &nbsp;|&nbsp; ');
                row.appendChild(crewDiv);
            }

            // Action row: Recommend Similar button
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'row-actions';

            const btnRec = document.createElement('button');
            btnRec.type = 'button';
            btnRec.className = 'btn-recommend';
            btnRec.textContent = 'Recommend Similar';
            btnRec.addEventListener('click', () => {
                requestRecommendations(item.id, item.title, item.release_year, item.media_type || state.engine);
            });

            actionsDiv.appendChild(btnRec);
            row.appendChild(actionsDiv);

            elements.resultsList.appendChild(row);
        });
    }

    function showLoading(show, message = 'Loading...') {
        if (show) {
            elements.loadingText.textContent = message;
            elements.loadingIndicator.classList.remove('hidden');
        } else {
            elements.loadingIndicator.classList.add('hidden');
        }
    }

    function showAlert(message, type = 'info') {
        elements.alertMessage.textContent = message;
        elements.alertBox.className = type === 'error' ? 'alert-banner error' : 'alert-banner';
        elements.alertBox.classList.remove('hidden');
    }

    function showRecommendationContext(title, year, mediaType, count) {
        state.activeRecommendationTarget = { title, year, mediaType };
        elements.targetTitle.textContent = title;
        elements.targetMeta.textContent = `(${year || 'N/A'}) • ${mediaType === 'tv' ? 'TV Series' : 'Movie'} • Content Similarity Model`;
        elements.recommendationContext.classList.remove('hidden');
    }

    function clearRecommendationContext() {
        state.activeRecommendationTarget = null;
        elements.recommendationContext.classList.add('hidden');
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Start on DOM ready
    document.addEventListener('DOMContentLoaded', init);
})();
