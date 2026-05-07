import React, { useState } from 'react';
import {
  Avatar,
  Group,
  Text,
  Menu,
  Divider,
  Badge,
} from '@mantine/core';
import { FaKey, FaSignOutAlt, FaEnvelope, FaShieldAlt, FaUser } from 'react-icons/fa';
import { useAuth } from '../../context/AuthContext';
import ChangePasswordModal from './ChangePasswordModal';

function ProfileHeader() {
  const { user, logout } = useAuth();
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);

  if (!user) return null;

  const handleLogout = async () => {
    await logout();
    globalThis.location.href = '/login';
  };

  return (
    <>
      <Menu position="left-start" withinPortal>
        <Menu.Target>
          <div
            style={{
              cursor: 'pointer',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              padding: '4px',
              borderRadius: '8px',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(34, 139, 230, 0.1)';
              e.currentTarget.style.transform = 'scale(1.05)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.transform = 'scale(1)';
            }}
          >
            <Avatar color="blue" radius="xl" size="lg">
              {user.username?.charAt(0).toUpperCase()}
            </Avatar>
          </div>
        </Menu.Target>

        <Menu.Dropdown style={{ minWidth: '280px' }}>
          {/* User Info Section */}
          <div style={{ padding: '12px', backgroundColor: '#fff5f5' }}>
            <Group spacing="sm" align="flex-start">
              <Avatar color="red" radius="xl" size="lg">
                {user.username?.charAt(0).toUpperCase()}
              </Avatar>
              <div style={{ flex: 1, minWidth: 0 }}>
                <Text size="sm" weight={700} style={{ textTransform: 'capitalize', color: '#c92a2a' }}>
                  {user.first_name} {user.last_name}
                </Text>
                <Text size="xs" c="dimmed" mt={2}>
                  <FaEnvelope size={12} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                  {user.email}
                </Text>
                <Group spacing="xs" mt="xs">
                  {user.roles && user.roles.length > 0 ? (
                    user.roles.slice(0, 2).map((role, index) => {
                      // Handle both string roles and object roles
                      const roleName = typeof role === 'string' ? role : role.name;
                      const roleType = typeof role === 'object' ? role.role_type : 'permanent';
                      const isEmergency = roleType === 'temporary';
                      const timeRemaining = typeof role === 'object' ? role.time_remaining : null;

                      return (
                        <div key={index}>
                          <Badge
                            size="sm"
                            color={isEmergency ? "orange" : "red"}
                            variant="filled"
                          >
                            {isEmergency && "⚡ "}
                            {roleName}
                          </Badge>
                          {isEmergency && timeRemaining && (
                            <Text size="xs" c="orange.7" fw={500} mt={2}>
                              ⏱️ {timeRemaining}
                            </Text>
                          )}
                        </div>
                      );
                    })
                  ) : (
                    <Badge size="sm" color="gray" variant="filled">
                      User
                    </Badge>
                  )}
                  {user.is_superuser && (
                    <Badge size="sm" color="darkred" variant="filled">
                      Super Admin
                    </Badge>
                  )}
                </Group>
              </div>
            </Group>
          </div>

          <Divider />

          {/* Menu Actions */}
          <Menu.Item
            icon={<FaUser size={16} />}
            onClick={() => {}}
            disabled
          >
            Profile Details
          </Menu.Item>

          <Menu.Item
            icon={<FaKey size={16} />}
            onClick={() => setPasswordModalOpen(true)}
          >
            Change Password
          </Menu.Item>

          <Divider />

          <Menu.Item
            icon={<FaSignOutAlt size={16} />}
            onClick={handleLogout}
            color="red"
          >
            Logout
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>

      {/* Change Password Modal */}
      <ChangePasswordModal
        opened={passwordModalOpen}
        onClose={() => setPasswordModalOpen(false)}
      />
    </>
  );
}

export default ProfileHeader;
