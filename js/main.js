document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.tombstone-container');
    const modalOverlay = document.querySelector('.modal-overlay');
    const modal = document.querySelector('.modal');
    const closeModalBtn = document.querySelector('.close-modal');
    const themeSwitcher = document.querySelector('.theme-switcher');
    const pageTitleElement = document.getElementById('page-title'); // 获取标题元素

    // 从全局变量中读取当前页面的数据和分页信息
    const allTombstones = window.PAGE_DATA || [];
    const currentPage = window.CURRENT_PAGE_NUMBER || 1;
    const totalPages = window.TOTAL_PAGES || 1;

    // --- 更新标题 ---
    if (pageTitleElement) {
        // 使用当前页码和总页数更新标题文本
        pageTitleElement.textContent = `Cyber Cemetery - Page ${currentPage}`;
        // 同时更新浏览器标签页上的标题
        document.title = `Cyber Cemetery - Page ${currentPage}`;
    } else {
        console.warn("Warning: Could not find element with id 'page-title'. Title will not be updated.");
    }

    // --- 加载 SVG 图标的辅助函数 ---
    async function loadSVG(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Failed to load SVG: ${url}`);
            }
            return await response.text();
        } catch (error) {
            console.error("Error loading SVG:", error);
            // 返回一个简单的错误图标 SVG，同样使用 currentColor
            return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';
        }
    }

    // --- 主题切换逻辑 ---
    async function toggleTheme() {
        document.body.classList.toggle('light-theme');
        const isLightTheme = document.body.classList.contains('light-theme');
        localStorage.setItem('theme', isLightTheme ? 'light' : 'dark');
        // 切换主题后，更新按钮图标和颜色
        updateThemeIcon(isLightTheme);
    }

    // --- 更新按钮图标的函数 ---
    async function updateThemeIcon(isLightTheme) {
        // 构造要加载的 SVG 文件路径
        const iconPath = isLightTheme ? 'assets/moon.svg' : 'assets/sun.svg';
        const svgContent = await loadSVG(iconPath);

        // 将 SVG 内容插入到按钮中
        themeSwitcher.innerHTML = svgContent;
        // 注意：现在我们不需要手动设置 SVG 的 stroke/fill 了，
        // 因为 CSS 已经通过 .theme-switcher svg { stroke: currentColor; fill: currentColor; }
        // 和 .theme-switcher { color: var(--theme-icon-dark-mode-color/--theme-icon-light-mode-color); }
        // 实现了颜色的自动切换。
        // 只需确保按钮的 color 属性反映了当前的主题。
        // 但是，由于 CSS 变量会根据 body 的类自动更新，我们只需更新 body 类，
        // CSS 规则就会自动应用正确的颜色到按钮上。
        // 所以这里只需要重新加载 SVG 即可，颜色会自动跟随主题变化。
        // 如果你想更精确地控制按钮的 color，也可以在这里设置：
        // themeSwitcher.style.color = getComputedStyle(themeSwitcher).getPropertyValue('--theme-icon-dark-mode-color').trim();
        // 但上面的 CSS 方法更优雅，因为它完全依赖于 CSS 变量。
    }

    // --- 初始化主题和图标 ---
    const savedTheme = localStorage.getItem('theme');
    const isLightThemeOnLoad = savedTheme === 'light';
    if (isLightThemeOnLoad) {
        document.body.classList.add('light-theme');
    }
    // 在 DOM 加载完成后立即更新图标
    updateThemeIcon(isLightThemeOnLoad);

    // 为切换器添加点击事件监听器
    themeSwitcher.addEventListener('click', toggleTheme);

    // --- 墓碑渲染逻辑 (现在只渲染当前页面的数据) ---
    function renderPage() {
        container.innerHTML = '';
        if (allTombstones.length === 0) {
            container.innerHTML = '<p>No tombstones found on this page.</p>';
            return;
        }

        allTombstones.forEach(tombstone => {
            const tombstoneEl = document.createElement('div');
            tombstoneEl.className = 'tombstone';
            tombstoneEl.dataset.id = tombstone.id;

            tombstoneEl.innerHTML = `
                <img src="${tombstone.avatar}" alt="${tombstone.name}'s avatar">
                <h3 class="name">${tombstone.name}</h3>
                <p class="id">ID: ${tombstone.id}</p>
            `;

            tombstoneEl.addEventListener('click', () => openModal(tombstone));
            container.appendChild(tombstoneEl);
        });
    }

    // --- 弹窗打开逻辑 ---
    function openModal(tombstone) {
        modalOverlay.style.display = 'block';
        modal.style.display = 'block';

        document.getElementById('modal-avatar').src = tombstone.avatar;
        document.getElementById('modal-name').textContent = tombstone.name;
        document.getElementById('modal-id').textContent = `ID: ${tombstone.id}`;

        // 新增：设置创建日期
        // 检查是否有 created 字段，如果有则显示，否则隐藏该元素
        const createdElement = document.getElementById('modal-created');
        if (tombstone.created) {
            // 可以根据需要格式化日期，这里直接显示原始字符串
            createdElement.textContent = `Created: ${tombstone.created}`;
            createdElement.style.display = ''; // 确保元素可见
        } else {
            createdElement.textContent = ''; // 清空内容
            createdElement.style.display = 'none'; // 如果没有日期，则隐藏
        }

        document.getElementById('modal-epitaph').textContent = tombstone.epitaph;

        const linksContainer = document.getElementById('modal-links');
        linksContainer.innerHTML = '';
        if (tombstone.links && tombstone.links.length > 0) {
            tombstone.links.forEach(link => {
                const linkEl = document.createElement('a');
                linkEl.href = link.url;
                linkEl.textContent = link.title;
                linkEl.target = "_blank";
                linkEl.rel = "noopener noreferrer";
                linksContainer.appendChild(linkEl);
            });
        } else {
            linksContainer.innerHTML = '<span>No links provided.</span>';
        }

        // 重新触发动画
        if (modal.classList.contains('active')) {
            modal.classList.remove('active');
        }
        if (modalOverlay.classList.contains('active')) {
            modalOverlay.classList.remove('active');
        }
        void modal.offsetWidth; void modalOverlay.offsetWidth;
        modalOverlay.classList.add('active');
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    // --- 弹窗关闭逻辑 ---
    function closeModal() {
        modalOverlay.classList.remove('active');
        modal.classList.remove('active');
        setTimeout(() => {
            if (!modal.classList.contains('active') && !modalOverlay.classList.contains('active')) {
                modalOverlay.style.display = 'none';
                modal.style.display = 'none';
            }
        }, 300);
        document.body.style.overflow = '';
    }

    // 点击遮罩层关闭弹窗
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) {
            closeModal();
        }
    });

    closeModalBtn.addEventListener('click', closeModal);

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });

    // 初始化页面 (渲染当前页数据)
    renderPage();

    // --- 分页导航生成逻辑 ---
    function createPagination() {
        const paginationContainer = document.querySelector('.pagination');
        paginationContainer.innerHTML = '';

        // 简单限制显示的页码数量，避免过多链接
        const maxVisiblePages = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

        // 调整起始页，确保始终显示 maxVisiblePages 个链接（如果可能）
        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        // 上一页链接
        if (currentPage > 1) {
            const prevLink = document.createElement('a');
            if (currentPage === 2) {
                prevLink.href = 'index.html'; // 第二页的上一页是 index.html
            } else {
                prevLink.href = `page_${currentPage - 1}.html`; // 例如：第3页的上一页是 page_2.html
            }
            prevLink.textContent = 'Previous';
            paginationContainer.appendChild(prevLink);
        }

        // 页码链接
        for (let i = startPage; i <= endPage; i++) {
            const pageLink = document.createElement('a');
            if (i === 1) {
                pageLink.href = 'index.html'; // 第一页总是 index.html
            } else {
                pageLink.href = `page_${i}.html`; // 第二页是 page_2.html, 第三页是 page_3.html ...
            }
            pageLink.textContent = i;
            if (i === currentPage) {
                pageLink.classList.add('active');
                pageLink.href = '#';
                pageLink.onclick = (e) => e.preventDefault();
            }
            paginationContainer.appendChild(pageLink);
        }

        // 下一页链接
        if (currentPage < totalPages) {
            const nextLink = document.createElement('a');
            nextLink.href = `page_${currentPage + 1}.html`; // 例如：第2页的下一页是 page_3.html
            nextLink.textContent = 'Next';
            paginationContainer.appendChild(nextLink);
        }
    }

    // 生成分页导航
    if (document.querySelector('.pagination')) {
        createPagination();
    }
});