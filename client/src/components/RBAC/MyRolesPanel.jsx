import React, { useState, useEffect } from 'react';
import {
  Stack,
  Paper,
  Title,
  Text,
  Badge,
  Loader,
  Alert,
  Group,
  ThemeIcon,
} from '@mantine/core';
import { IconShield, IconBan, IconLock } from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import { useAuth } from '../../context/AuthContext';

import { getUserRoles, getUserStatus, checkUserAccess } from '../../services/rbacService';

function MyRolesPanel() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [userRoles, setUserRoles] = useState([]);
  const [userStatus, setUserStatus] = useState(null);
  const [canAccess, setCanAccess] = useState(true);
  const [accessCheck, setAccessCheck] = useState(null);

  useEffect(() => {
    if (user?.username) {
      fetchMyData();
    }
  }, [user]);

  const fetchMyData = async () => {
    try {
      setLoading(true);

      const rolesData = await getUserRoles(user.username);
      setUserRoles(rolesData.roles || []);

      const statusData = await getUserStatus(user.username);
      setUserStatus(statusData);

      const accessData = await checkUserAccess(user.username);
      setCanAccess(accessData.can_access);
      setAccessCheck(accessData);

      if (!accessData.can_access) {
        showNotification({
          title: 'Access Denied',
          message: accessData.error || 'You cannot access the system',
          color: 'red',
          autoClose: 10000,
        });
      }
    } catch (error) {
      console.error('Error fetching my data:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to load your roles and status',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Stack align="center" p="xl">
        <Loader />
        <Text size="sm" c="dimmed">Loading your roles...</Text>
      </Stack>
    );
  }

  return (
    <Stack>
      <Title order={3}>My Roles & Status</Title>

      <Alert
        icon={userStatus?.is_blocked ? <IconBan /> : <IconShield />}
        color={userStatus?.is_blocked ? 'red' : 'green'}
        title={`Account Status: ${userStatus?.is_blocked ? 'BLOCKED' : 'ACTIVE'}`}
      >
        <Stack spacing="xs">
          <Text size="sm" component="div"><strong>Username:</strong> {user?.username}</Text>
          <Text size="sm" component="div">
            <strong>Status:</strong>{' '}
            {userStatus?.is_blocked ? (
              <Badge color="red">BLOCKED - You cannot access the system</Badge>
            ) : (
              <Badge color="green">ACTIVE - You have full access</Badge>
            )}
          </Text>
          {userStatus?.is_blocked && (
            <Text size="sm" c="red" component="div">
              <strong>Action Required:</strong> Contact system administrator to unblock your account.
            </Text>
          )}
        </Stack>
      </Alert>

      <Paper shadow="xs" p="md" withBorder>
        <Group justify="space-between" mb="sm">
          <Title order={5}>Assigned Roles ({userRoles.length})</Title>
        </Group>

        {userRoles.length === 0 ? (
          <Text ta="center" c="dimmed" py="md">
            No roles assigned. Contact administrator.
          </Text>
        ) : (
          <Stack>
            {userRoles.map((role) => (
              <Group 
                key={`${role.name}-${role.id}`} 
                p="md" 
                bg={role.role_type === 'temporary' ? 'orange.0' : 'gray.0'} 
                radius="sm" 
                justify="space-between"
                style={{
                  border: role.role_type === 'temporary' ? '2px solid #ff922b' : '1px solid #e9ecef'
                }}
              >
                <Stack gap={4}>
                  <Group gap="xs">
                    <ThemeIcon color={role.role_type === 'temporary' ? "orange" : "blue"} size="lg">
                      <IconShield size={20} />
                    </ThemeIcon>
                    <Stack gap={0}>
                      <Group gap="xs">
                        <Text fw={600} size="lg">{role.name}</Text>
                        {role.role_type === 'temporary' && (
                          <Badge color="orange" variant="filled" leftSection={<IconShield size={12} />}>
                            {role.temporary_tag || 'EMERGENCY ACCESS'}
                          </Badge>
                        )}
                        {role.role_type === 'permanent' && (
                          <Badge color="green" variant="filled">
                            {role.permanent_tag || 'PERMANENT'}
                          </Badge>
                        )}
                      </Group>
                      {role.full_name && (
                        <Text size="sm" c="dimmed">{role.full_name}</Text>
                      )}
                      {role.role_type === 'temporary' && role.time_remaining && (
                        <Text size="sm" c="orange.7" fw={600}>
                          ⏱️ Expires in: {role.time_remaining}
                        </Text>
                      )}
                      {role.role_type === 'temporary' && role.expires_at && (
                        <Text size="xs" c="dimmed">
                          Expiry time: {new Date(role.expires_at).toLocaleString()}
                        </Text>
                      )}
                      {role.role_type === 'temporary' && role.approved_duration_minutes && (
                        <Text size="xs" c="dimmed">
                          Granted duration: {Math.floor(role.approved_duration_minutes / 60)}h {role.approved_duration_minutes % 60}m
                        </Text>
                      )}
                    </Stack>
                  </Group>
                </Stack>
                <Stack gap="xs" align="end">
                  <Badge color={role.role_type === 'temporary' ? "orange" : "blue"}>
                    {role.category || 'role'}
                  </Badge>
                  {role.role_type === 'temporary' && (
                    <Badge color="red" variant="outline" size="xs">
                      Auto-Expiring
                    </Badge>
                  )}
                  {role.role_type === 'permanent' && (
                    <Badge color="green" variant="outline" size="xs">
                      No Expiry
                    </Badge>
                  )}
                </Stack>
              </Group>
            ))}
          </Stack>
        )}
      </Paper>

      {accessCheck && (
        <Alert color={canAccess ? 'green' : 'red'}>
          <Text size="sm">
            <strong>System Access:</strong>{' '}
            {canAccess ? (
              'You have full system access'
            ) : (
              `Access Denied: ${accessCheck.error || 'Contact administrator'}`
            )}
          </Text>
        </Alert>
      )}
    </Stack>
  );
}

export default MyRolesPanel;
