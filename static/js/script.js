////// SHARED HELPERS //////

// Updates hidden input
function updateHiddenInput(modal) {
    const tags = Array.from(modal.querySelectorAll('.category-tag-text')).map(span => span.textContent);
    modal.querySelector('input[name="final_categories"]').value = tags.join(',');
}

// Adds visual category tags to modals
function addTagUI(modal, val) {
    if (!val || val.toLowerCase() === 'default') return;
    const existing = Array.from(modal.querySelectorAll('.category-tag-text')).map(span => span.textContent);
    if (existing.includes(val)) return;

    const tagsContainer = modal.querySelector('.category-tags-container');
    const tag = document.createElement('span');
    tag.className = 'badge bg-info text-dark d-flex align-items-center gap-2 mb-2';
    tag.innerHTML = `<span class="category-tag-text">${val}</span> <button type="button" class="btn-close" style="font-size: 0.5rem;"></button>`;
    
    tag.querySelector('.btn-close').addEventListener('click', () => {
        tag.remove();
        updateHiddenInput(modal);
    });

    tagsContainer.appendChild(tag);
    updateHiddenInput(modal);
}

// Makes tags for the search bar (Input Box)
function updateSearchCategoryTag(catName) {
    const container = document.getElementById('search-category-tags-container');
    const input = document.getElementById('filter-category');
    
    // Prevent duplicates
    const existing = Array.from(container.querySelectorAll('.category-tag-text')).map(span => span.textContent);
    if (existing.includes(catName) || !catName) return;

    const tag = document.createElement('span');
    tag.className = 'badge bg-primary d-inline-flex align-items-center gap-2 p-2';
    tag.innerHTML = `<span class="category-tag-text">${catName}</span> 
                     <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;"></button>`;
    
    tag.querySelector('.btn-close').onclick = () => {
        tag.remove();
        performSearch();
        toggleSortable();
    };

    container.appendChild(tag);
    input.value = ''; 
}

// Clickable badges on recipe cards
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('category-filter-btn')) {
        const catName = e.target.textContent.trim();
        const container = document.getElementById('search-category-tags-container');
        
        const existingTags = Array.from(container.querySelectorAll('.category-tag-text'));
        const activeTag = existingTags.find(span => span.textContent === catName);

        if (activeTag) {
            activeTag.closest('.badge').remove();
        } else {
            updateSearchCategoryTag(catName);
        }

        performSearch();
        toggleSortable();
    }
});

// Adds ingredient rows to modals
function addIngredientRow(modal, qty = '', meas_id = 1, name = '') {
    const container = modal.querySelector('.ingredient-container');
    const row = document.createElement('div');
    row.className = 'row g-2 mb-2 ingredient-row';
    const masterSelect = document.querySelector('select[name="measurements[]"]');
    const optionsHtml = masterSelect ? masterSelect.innerHTML : '';
    
    row.innerHTML = `
        <div class="col-3"><input type="number" step="0.1" name="quantities[]" class="form-control" value="${qty}" required></div>
        <div class="col-3"><select name="measurements[]" class="form-control">${optionsHtml}</select></div>
        <div class="col-5"><input type="text" name="ingredients[]" class="form-control" value="${name}" required></div>
        <div class="col-1"><button type="button" class="btn btn-outline-danger btn-sm remove-row">×</button></div>
    `;
    row.querySelector('select').value = meas_id;
    container.appendChild(row);
}

////// INSTANT SEARCH LOGIC //////

function performSearch() {
    const nameEl = document.getElementById('search-name');
    const ingredEl = document.getElementById('search-ingredient');
    const container = document.getElementById('recipes-container');
    const activeCategories = Array.from(document.querySelectorAll('#search-category-tags-container .category-tag-text'))
                                  .map(span => span.textContent);

    const params = new URLSearchParams({
        name: nameEl.value,
        ingredient: ingredEl.value,
        categories: activeCategories.join(',')
    });

    fetch(`/search-recipes?${params.toString()}`)
        .then(res => res.text())
        .then(html => {
            container.innerHTML = html;

            document.querySelectorAll('.category-filter-btn').forEach(btn => {
                if (activeCategories.includes(btn.textContent.trim())) {
                    btn.classList.replace('bg-info', 'bg-primary');
                } else {
                    btn.classList.replace('bg-primary', 'bg-info');
                }
            });
        });
}

function debounce(func, timeout = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}
const processSearch = debounce(() => performSearch());

// Clear filters
function resetFilters() {
    document.getElementById('search-name').value = '';
    document.getElementById('search-ingredient').value = '';
    document.getElementById('filter-category').value = '';
    const tagContainer = document.getElementById('search-category-tags-container');
    if (tagContainer) {
        tagContainer.innerHTML = '';
    }
    performSearch();
    toggleSortable();
}

const clearFiltersButton = document.getElementById('btn-clear-filters');

clearFiltersButton.addEventListener('click', function(e) {
    resetFilters()
});

// Search Event Listeners
document.getElementById('search-name').addEventListener('input', () => { processSearch(); toggleSortable(); });
document.getElementById('search-ingredient').addEventListener('input', () => { processSearch(); toggleSortable(); });

// Category Input with Datalis  t validation
const categorySearchInput = document.getElementById('filter-category');
categorySearchInput.addEventListener('input', function(e) {
    const val = e.target.value;
    const options = Array.from(document.getElementById('search-category-options').options).map(o => o.value);

    if (options.includes(val)) {
        updateSearchCategoryTag(val);
        performSearch();
        toggleSortable();
    }
});

////// MODAL EVENT LISTENERS //////

document.querySelectorAll('.modal').forEach(modal => {
    const addIngBtn = modal.querySelector('.btn-add-ingredient');
    if (addIngBtn) {
        addIngBtn.onclick = () => addIngredientRow(modal);
    }
    const catInput = modal.querySelector('.category-input-field');
    const addCatBtn = modal.querySelector('.btn-add-category');
    if (addCatBtn && catInput) {
        const handleAdd = () => {
            addTagUI(modal, catInput.value.trim());
            catInput.value = '';
        };
        addCatBtn.onclick = handleAdd;
        catInput.onkeypress = (e) => { if (e.key === 'Enter') { e.preventDefault(); handleAdd(); } };
    }
});

const editModal = document.getElementById('editRecipeModal');
editModal.addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget;
    const recipeId = button.getAttribute('data-bs-id');
    fetch(`/get-recipe/${recipeId}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('edit-recipe-id').value = recipeId;
            document.getElementById('edit-name').value = data.name || "";
            document.getElementById('edit-desc').value = data.desc || "";
            document.getElementById('edit-steps').value = data.steps || "";

            const tagContainer = editModal.querySelector('.category-tags-container');
            if (tagContainer) {
                tagContainer.innerHTML = '';
                if (data.categories) data.categories.forEach(cat => addTagUI(editModal, cat));
            }

            const ingContainer = editModal.querySelector('.ingredient-container');
            if (ingContainer) {
                ingContainer.innerHTML = '';
                if (data.ingredients && data.ingredients.length > 0) {
                    data.ingredients.forEach(ing => addIngredientRow(editModal, ing.qty, ing.meas_id, ing.name));
                } else {
                    addIngredientRow(editModal);
                }
            }
        });
});

// Global Remove Row listener
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('remove-row')) {
        const row = e.target.closest('.ingredient-row');
        const container = e.target.closest('.ingredient-container');
        if (container && container.querySelectorAll('.ingredient-row').length > 1) {
            row.remove();
        }
    }
});

////// SORTABLE CARDS //////

const recipesContainer = document.getElementById('recipes-container');
const sortable = new Sortable(recipesContainer, {
    animation: 150,
    ghostClass: 'sortable-ghost',
    draggable: '.col-md-4',
    filter: '.no-drag, button, input, select',
    onMove: function (evt) { return !evt.related.classList.contains('no-drag'); },
    onEnd: function () {
        const recipeIds = Array.from(recipesContainer.querySelectorAll('[data-bs-id]'))
                               .map(btn => btn.getAttribute('data-bs-id'));
        fetch('/update-recipe-order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name="csrf_token"]').value
            },
            body: JSON.stringify({ ids: recipeIds })
        });
    }
});

function toggleSortable() {
    const isSearching = document.getElementById('search-name').value.length > 0 || 
                        document.getElementById('search-ingredient').value.length > 0 || 
                        document.getElementById('filter-category').value !== "";
    sortable.option("disabled", isSearching);
}