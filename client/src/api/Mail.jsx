import apiClient from '../services/api';

export const mailBatch = async (batch) => {
    try {
        const response = await apiClient.post('/users/mail-batch/', {
            batch: batch,
        });
        return response.data;
    } catch (error) {
        console.error('Error mailing users:', error.response?.data || error.message);
        throw error;
    }
};
