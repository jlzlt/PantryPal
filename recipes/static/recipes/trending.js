document.addEventListener('DOMContentLoaded', function() {
    const loadMoreBtn = document.getElementById('load-more');
    if (!loadMoreBtn) return;
    
    let currentPage = 1;
    let isLoading = false;
    
    loadMoreBtn.addEventListener('click', async function() {
        if (isLoading) return;
        
        isLoading = true;
        currentPage++;
        
        try {
            const response = await fetch(`?page=${currentPage}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            // Add new recipes to the grid
            const recipeGrid = document.getElementById('recipe-grid');
            recipeGrid.insertAdjacentHTML('beforeend', data.html);
            
            // Hide load more button if no more recipes
            if (!data.has_more) {
                loadMoreBtn.style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading more recipes:', error);
            alert('An error occurred while loading more recipes.');
        } finally {
            isLoading = false;
        }
    });
}); 