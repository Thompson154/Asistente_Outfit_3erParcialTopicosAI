// Outfit Assistant - Main JavaScript

// Utility function to show notifications
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Utility function to show loading spinner
function showLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loading-overlay';
    loadingDiv.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    loadingDiv.innerHTML = '<div class="loading-spinner"></div>';
    document.body.appendChild(loadingDiv);
}

function hideLoading() {
    const loading = document.getElementById('loading-overlay');
    if (loading) {
        loading.remove();
    }
}

// API helper functions
const API = {
    async uploadImage(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/clothes/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        
        return await response.json();
    },
    
    async saveClothing(imagePath, name, tags) {
        const formData = new FormData();
        formData.append('image_path', imagePath);
        formData.append('name', name);
        formData.append('tags', JSON.stringify(tags));
        
        const response = await fetch('/api/clothes', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Save failed');
        }
        
        return await response.json();
    },
    
    async getAllClothes() {
        const response = await fetch('/api/clothes');
        if (!response.ok) {
            throw new Error('Failed to fetch clothes');
        }
        return await response.json();
    },
    
    async deleteClothing(id) {
        const response = await fetch(`/api/clothes/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Delete failed');
        }
        
        return await response.json();
    },
    
    async generateOutfit(occasion, preferences = '') {
        const response = await fetch('/api/outfits/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ occasion, preferences })
        });
        
        if (!response.ok) {
            throw new Error('Generation failed');
        }
        
        return await response.json();
    },
    
    async saveOutfit(name, clothingIds, occasion = '') {
        const response = await fetch('/api/outfits', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                clothing_ids: clothingIds,
                occasion
            })
        });
        
        if (!response.ok) {
            throw new Error('Save failed');
        }
        
        return await response.json();
    },
    
    async getSavedOutfits() {
        const response = await fetch('/api/outfits');
        if (!response.ok) {
            throw new Error('Failed to fetch outfits');
        }
        return await response.json();
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API, showNotification, showLoading, hideLoading };
}
