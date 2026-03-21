document.addEventListener("DOMContentLoaded", () => {

    /* =========================
       LIKE BUTTON
    ========================== */
    document.querySelectorAll(".like-btn").forEach(btn => {
        const heart = btn.querySelector(".heart");
        const countEl = btn.querySelector(".like-count");
        if (!heart || !countEl) return;

        btn.addEventListener("click", () => {
            const liked = btn.dataset.liked === "true";
            const count = parseInt(countEl.textContent) || 0;

            heart.textContent = liked ? "🤍" : "❤️";
            countEl.textContent = liked ? count - 1 : count + 1;
            btn.dataset.liked = (!liked).toString();
        });
    });

    /* =========================
       FOLLOW BUTTON
    ========================== */
    document.querySelectorAll(".user button").forEach(btn => {
        btn.addEventListener("click", () => {
            const following = btn.classList.toggle("following");
            btn.textContent = following ? "Following" : "Follow";
        });
    });

    /* =========================
       SIDEBAR ACTIVE MENU
    ========================== */
    document.querySelectorAll(".menu-link").forEach(link => {
        link.addEventListener("click", () => {
            document.querySelectorAll(".menu-link")
                .forEach(l => l.classList.remove("active"));
            link.classList.add("active");
        });
    });

    /* =========================================
       SETTINGS DROPDOWN & LOGOUT MODAL
    ========================================= */
    const toggleBtn = document.getElementById('settingsToggle');
    const menu = document.getElementById('settingsMenu');
    const logoutTrigger = document.getElementById('logoutTrigger');
    const logoutModal = document.getElementById('logoutModal');
    const cancelLogout = document.getElementById('cancelLogout');

    if (toggleBtn && menu) {
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            menu.classList.toggle('show');
        });
        document.addEventListener('click', () => menu.classList.remove('show'));
    }

    if (logoutTrigger) {
        logoutTrigger.addEventListener('click', () => {
            logoutModal?.classList.add('active');
        });
    }

    if (cancelLogout) {
        cancelLogout.addEventListener('click', () => {
            logoutModal?.classList.remove('active');
        });
    }

    /* =========================================
       NOTIFICATION PANEL LOGIC
    ========================================= */
    const notifLink = document.querySelector('a[href*="notifications"]');
    const panel = document.getElementById('notificationPanel');

    if (notifLink && panel) {
        notifLink.addEventListener("click", function(e) {
            e.preventDefault();
            panel.classList.toggle('active');
            const badge = document.querySelector('.notification-badge');
            if (badge) badge.style.display = 'none';
        });

        // Close panel when clicking outside
        document.addEventListener("click", (e) => {
            if (!panel.contains(e.target) && !notifLink.contains(e.target)) {
                panel.classList.remove('active');
            }
        });
    }

    /* =========================================
       SEARCH LOGIC (SIDEBAR REDIRECT & LIVE AJAX)
    ========================================= */
    const topSearchInput = document.getElementById("topSearchInput");
    const searchDropdown = document.getElementById("searchDropdown");
    const searchDropdownContent = document.querySelector(".search-dropdown-content");
    const sidebarSearchBtn = document.getElementById("searchBtn");

    // 1. Catch redirect from another page (e.g., Profile page)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('action') === 'search' && topSearchInput) {
        setTimeout(() => {
            topSearchInput.focus();
        }, 150);
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    // 2. Sidebar Search Button Click Logic
    if (sidebarSearchBtn) {
        sidebarSearchBtn.addEventListener("click", function(e) {
            e.preventDefault();
            if (topSearchInput) {
                window.scrollTo({ top: 0, behavior: 'smooth' });
                topSearchInput.focus();
            } else {
                window.location.href = "/?action=search"; 
            }
        });
    }

    // 3. Main Search Bar Dropdown & AJAX Fetch
    if (topSearchInput && searchDropdown) {
        
        // Show dropdown when focused
        topSearchInput.addEventListener("focus", function() {
            searchDropdown.classList.add("show");
        });

        // Hide dropdown when clicking completely outside
        document.addEventListener("click", function(e) {
            const isClickInside = topSearchInput.contains(e.target) || searchDropdown.contains(e.target);
            const isSidebarBtn = sidebarSearchBtn && sidebarSearchBtn.contains(e.target);
            
            if (!isClickInside && !isSidebarBtn) {
                searchDropdown.classList.remove("show");
            }
        });

        // Live AJAX Search 
        let timeout = null;
        topSearchInput.addEventListener("input", function() {
            clearTimeout(timeout); 
            const query = this.value.trim();

            if (query.length > 0) {
                timeout = setTimeout(() => {
                    searchDropdownContent.innerHTML = '<p class="no-recent" style="color:#888;">Searching...</p>';

                    fetch(`/live-search/?q=${encodeURIComponent(query)}`)
                        .then(response => response.json())
                        .then(data => {
                            searchDropdownContent.innerHTML = ''; 
                            
                            if (data.results.length > 0) {
                                data.results.forEach(user => {
                                    const imageHtml = user.profile_image 
                                        ? `<img src="${user.profile_image}" style="width:40px; height:40px; border-radius:50%; object-fit:cover;">`
                                        : `<div style="width:40px; height:40px; border-radius:50%; background-color:#333; display:flex; align-items:center; justify-content:center;"><i class='bx bx-user' style="color:#888;"></i></div>`;

                                    const userRow = `
                                        <div style="display:flex; align-items:center; margin-bottom:15px; padding: 5px; border-radius: 5px; transition: background 0.2s;">
                                            <a href="/p/${user.id}/" style="text-decoration:none; color:inherit; display:flex; align-items:center; gap:10px; width:100%;">
                                                ${imageHtml}
                                                <div style="font-weight:600; font-size:14px; color:#fff;">${user.username}</div>
                                            </a>
                                        </div>
                                    `;
                                    searchDropdownContent.insertAdjacentHTML('beforeend', userRow);
                                });
                            } else {
                                searchDropdownContent.innerHTML = '<p class="no-recent" style="color:#888;">No users found.</p>';
                            }
                        })
                        .catch(error => console.error("Error fetching search results:", error));
                }, 300); 

            } else {
                searchDropdownContent.innerHTML = '<p class="no-recent" style="color:#888;">Type to search users...</p>';
            }
        });
    }
    

});