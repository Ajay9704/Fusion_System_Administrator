import apiClient from '../services/api';

console.log('API Client configured for password reset and user management');

export const createUser = async (userData) => {
    try {
        const response = await apiClient.post('/users/add/', userData);
        return response.data;
    } catch (error) {
        console.error('Error creating user:', error.response?.data || error.message);
        throw error;
    }
};

export const createStudent = async (userData) => {
    try {
        const response = await apiClient.post('/users/add-student/', userData);
        return response.data;
    } catch (error) {
        console.error(`Error creating student: ${error.response?.data || error.message}`);
        throw error;
    }
}

export const createFaculty = async (userData) => {
    try {
        const response = await apiClient.post('/users/add-faculty/', userData);
        return response.data;
    } catch (error) {
        console.error('Error creating faculty:', error.response?.data || error.message);
        throw error;
    }
}

export const createStaff = async (userData) => {
    try {
        const response = await apiClient.post('/users/add-staff/', userData);
        return response.data;
    } catch (error) {
        console.error('Error creating staff:', error.response?.data || error.message);
        throw error;
    }
}

export const resetPassword = async (userData) => {
    try {
        const response = await apiClient.post('/users/reset_password/', userData);
        return response.data;
    } catch (error) {
        console.error('Error resetting password:', error.response?.data || error.message);
        throw error;
    }
}

export const bulkUploadUsers = async (userData) => {
    try {
        const response = await apiClient.post('/users/import/', userData);
        return response.data;
    } catch (error) {
        console.error('Error uploading users:', error.response?.data || error.message);
        throw error;
    }
}

export const downloadSampleCSV = async () => {
    try {
      const response = await apiClient.get('/download-sample-csv', {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'sample.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error fetching sample CSV:', error.response?.data || error.message);
      throw error;
    }
};

export const fetchUsersByType = async (type) => {
    try {
        const response = await apiClient.get(`/users?type=${type}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching users:', error.response?.data || error.message);
        throw error;
    }
};
