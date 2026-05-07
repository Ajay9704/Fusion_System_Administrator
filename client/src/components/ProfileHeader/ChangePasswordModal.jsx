import React, { useState } from 'react';
import {
  Modal,
  Stack,
  PasswordInput,
  Button,
  Group,
  Text,
  Alert,
  Loader,
} from '@mantine/core';
import { FaCheck, FaTimes, FaKey } from 'react-icons/fa';
import { rem } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { changePassword } from '../../services/authService';

function ChangePasswordModal({ opened, onClose }) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const checkIcon = <FaCheck style={{ width: rem(20), height: rem(20) }} />;
  const xIcon = <FaTimes style={{ width: rem(20), height: rem(20) }} />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      setError('All fields are required');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (currentPassword === newPassword) {
      setError('New password must be different from current password');
      return;
    }

    setLoading(true);

    try {
      // Change password using the authenticated endpoint
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });

      showNotification({
        icon: checkIcon,
        title: 'Success',
        message: 'Your password has been changed successfully',
        position: 'top-center',
        withCloseButton: true,
        autoClose: 5000,
        color: 'green',
      });

      // Reset form and close modal
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      onClose();
    } catch (err) {
      console.error('Password change error:', err);
      
      const errorMessage = err.response
        ? `${err.response.data.error || 'Failed to change password'}`
        : err.request
        ? 'No response received from the server'
        : `${err.message}`;

      setError(errorMessage);
      
      showNotification({
        icon: xIcon,
        title: 'Error',
        message: errorMessage,
        position: 'top-center',
        withCloseButton: true,
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setError(null);
    onClose();
  };

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title={
        <Group spacing="sm">
          <FaKey size={20} />
          <Text weight={600}>Change Password</Text>
        </Group>
      }
      size="md"
      centered
    >
      <form onSubmit={handleSubmit}>
        <Stack spacing="md">
          {error && (
            <Alert icon={xIcon} title="Error" color="red">
              {error}
            </Alert>
          )}

          <PasswordInput
            label="Current Password"
            placeholder="Enter your current password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
            disabled={loading}
          />

          <PasswordInput
            label="New Password"
            placeholder="Enter new password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            disabled={loading}
            description="Must be at least 8 characters"
          />

          <PasswordInput
            label="Confirm New Password"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            disabled={loading}
          />

          <Group position="right" spacing="sm" mt="md">
            <Button variant="outline" onClick={handleClose} disabled={loading}>
              Cancel
            </Button>
            <Button
              type="submit"
              loading={loading}
              loaderPosition="center"
              leftIcon={loading ? <Loader size="xs" /> : <FaKey size={16} />}
            >
              {loading ? 'Updating...' : 'Update Password'}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

export default ChangePasswordModal;
