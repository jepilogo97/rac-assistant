/**
 * Formatter utilities
 */

export const formatNumber = (num) => {
    if (num === null || num === undefined) return '0';
    return new Intl.NumberFormat('es-CO').format(num);
};

export const formatDecimal = (num, decimals = 2) => {
    if (num === null || num === undefined) return '0.00';
    return new Intl.NumberFormat('es-CO', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    }).format(num);
};

export const formatPercentage = (num, decimals = 1) => {
    if (num === null || num === undefined) return '0%';
    return `${formatDecimal(num, decimals)}%`;
};

export const formatTime = (minutes) => {
    if (!minutes) return '0 min';

    if (minutes < 60) {
        return `${formatDecimal(minutes, 0)} min`;
    }

    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;

    if (mins === 0) {
        return `${hours}h`;
    }

    return `${hours}h ${formatDecimal(mins, 0)}min`;
};

export const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

export const formatDate = (date) => {
    return new Intl.DateTimeFormat('es-CO', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    }).format(new Date(date));
};
