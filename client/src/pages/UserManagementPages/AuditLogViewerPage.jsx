import React, { useState, useEffect } from 'react';
import {
  Container,
  Title,
  Paper,
  Table,
  Group,
  Text,
  Badge,
  TextInput,
  Button,
  Select,
  Stack,
  Pagination,
  Loader,
  Center,
  Alert,
  ActionIcon,
  Tooltip,
  Modal,
  Code,
  ScrollArea,
  Spoiler,
} from '@mantine/core';
import { IconSearch, IconFilter, IconAlertCircle, IconClock, IconRefresh, IconDeviceDesktop, IconInfoCircle, IconDownload } from '@tabler/icons-react';
import api from '../../services/api';
import { getActionStatusDisplay } from '../../utils/erpMessages';

function AuditLogViewerPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [username, setUsername] = useState('');
  const [action, setAction] = useState('');
  const [status, setStatus] = useState('');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(50);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Detail modal
  const [selectedLog, setSelectedLog] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);

  const fetchAuditLogs = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {
        page: currentPage,
        page_size: pageSize,
      };

      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (username) params.user = username;
      if (action) params.action = action;
      if (status) params.status = status;

      const response = await api.get('/audit-logs/', { params });

      setLogs(response.data.results);
      setTotalCount(response.data.count);
      setTotalPages(response.data.total_pages);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching audit logs:', err);
      setError('Failed to fetch audit logs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();

    // Auto-refresh every 45 seconds for real-time ERP standards
    // This balances between real-time updates and server load
    const interval = setInterval(fetchAuditLogs, 45000);

    // Cleanup interval on unmount
    return () => clearInterval(interval);
  }, [currentPage, startDate, endDate, username, action, status]);

  const handleFilter = () => {
    setCurrentPage(1);
    fetchAuditLogs();
  };

  const handleReset = () => {
    setStartDate('');
    setEndDate('');
    setUsername('');
    setAction('');
    setStatus('');
    setCurrentPage(1);
  };

  const handleRefresh = () => {
    fetchAuditLogs();
  };

  const handleViewDetails = (log) => {
    setSelectedLog(log);
    setDetailModalOpen(true);
  };

  const exportToCSV = () => {
    if (logs.length === 0) return;

    const headers = ['Timestamp', 'User', 'Action', 'Model', 'Description', 'IP Address', 'User Agent', 'Status'];
    const csvContent = [
      headers.join(','),
      ...logs.map(log => [
        log.timestamp,
        log.user_username || 'N/A',
        log.action,
        log.model_name || 'N/A',
        `"${log.description.replace(/"/g, '""')}"`,
        log.ip_address || 'N/A',
        `"${(log.user_agent || 'N/A').replace(/"/g, '""')}"`,
        log.status
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_logs_${new Date().toISOString()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getStatusDisplay = (status) => {
    return getActionStatusDisplay(status);
  };

  const formatDescription = (description) => {
    // Enhanced descriptions already contain emojis and proper formatting from backend
    // Just need to display them properly
    if (!description) return '';

    // Split by pipe separator for multi-part descriptions
    const parts = description.split(' | ').map(part => part.trim());

    return parts;
  };

  const getActionBadgeColor = (action) => {
    // Color coding based on action type
    if (action.includes('CREATE') || action.includes('RESTORE')) return 'green';
    if (action.includes('DELETE') || action.includes('ARCHIVE') || action.includes('REVOKE')) return 'red';
    if (action.includes('UPDATE') || action.includes('CHANGE')) return 'blue';
    if (action.includes('FAILED') || action.includes('ERROR')) return 'red';
    if (action.includes('LOGIN') || action.includes('LOGOUT')) return 'gray';
    if (action.includes('EMERGENCY')) return 'orange';
    return 'blue';
  };

  return (
    <Container fluid style={{ padding: '20px' }}>
      <Stack spacing="md">
        <Group position="apart">
          <Title order={2}>System Audit Logs</Title>
          <Group spacing="md">
            {lastUpdated && (
              <Group spacing="xs">
                <Text size="xs" color="dimmed">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </Text>
                <Badge size="xs" color="green" variant="light">
                  Auto-refresh: 45s
                </Badge>
              </Group>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              leftSection={<IconRefresh size={16} />}
            >
              Refresh
            </Button>
            <Badge size="lg" variant="outline">
              Total: {totalCount} logs
            </Badge>
          </Group>
        </Group>

        {/* Filters */}
        <Paper shadow="sm" p="md" withBorder>
          <Group position="apart" mb="md">
            <Text size="sm" weight={500}>
              <IconFilter size={16} style={{ marginRight: '8px' }} />
              Filters
            </Text>
            <Button variant="subtle" size="xs" onClick={handleReset}>
              Reset Filters
            </Button>
          </Group>
          
          <Group grow>
            <TextInput
              label="Start Date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
            <TextInput
              label="End Date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
            <TextInput
              label="Username"
              placeholder="Search by username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </Group>
          
          <Group grow mt="md">
            <Select
              label="Action Type"
              placeholder="All Actions"
              value={action}
              onChange={setAction}
              clearable
              searchable
              data={[
                { value: '', label: 'All Actions' },
                { value: 'USER_LOGIN', label: 'User Login' },
                { value: 'USER_LOGOUT', label: 'User Logout' },
                { value: 'CREATE_STUDENT', label: 'Create Student' },
                { value: 'CREATE_FACULTY', label: 'Create Faculty' },
                { value: 'CREATE_STAFF', label: 'Create Staff' },
                { value: 'CREATE_ROLE', label: 'Create Role' },
                { value: 'UPDATE_ROLE', label: 'Update Role' },
                { value: 'UPDATE_USER_ROLES', label: 'Update User Roles' },
                { value: 'RESET_PASSWORD', label: 'Reset Password' },
                { value: 'BULK_IMPORT_USERS', label: 'Bulk Import Users' },
              ]}
            />
            <Select
              label="Status"
              placeholder="All"
              value={status}
              onChange={setStatus}
              data={[
                { value: '', label: 'All' },
                { value: 'SUCCESS', label: 'Success' },
                { value: 'FAILED', label: 'Failed' },
              ]}
            />
            <div style={{ marginTop: 'auto' }}>
              <Button
                onClick={handleFilter}
                fullWidth
                leftSection={<IconSearch size={16} />}
              >
                Apply Filters
              </Button>
            </div>
          </Group>
        </Paper>

        {/* Error Alert */}
        {error && (
          <Alert icon={<IconAlertCircle size={16} />} title="Error" color="red">
            {error}
          </Alert>
        )}

        {/* Audit Logs Table */}
        <Paper shadow="sm" withBorder>
          {loading ? (
            <Center style={{ height: 400 }}>
              <Loader size="lg" />
            </Center>
          ) : logs.length === 0 ? (
            <Center style={{ height: 400 }}>
              <Stack align="center">
                <IconClock size={48} style={{ opacity: 0.3 }} />
                <Text color="dimmed">No audit logs found</Text>
                <Text size="sm" color="dimmed">
                  Try adjusting your filters or check back later
                </Text>
              </Stack>
            </Center>
          ) : (
            <>
              <Table horizontalSpacing="md" verticalSpacing="sm" striped highlightOnHover>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Model</th>
                    <th>Description</th>
                    <th>IP Address</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id}>
                      <td>
                        <Text size="sm">{formatTimestamp(log.timestamp)}</Text>
                      </td>
                      <td>
                        {log.user_username ? (
                          <Text size="sm" weight={500}>
                            {log.user_username}
                          </Text>
                        ) : (
                          <Text size="sm" color="dimmed">
                            System
                          </Text>
                        )}
                      </td>
                      <td>
                        <Badge
                          size="sm"
                          color={getActionBadgeColor(log.action)}
                          variant="light"
                        >
                          {log.action.replace(/_/g, ' ')}
                        </Badge>
                      </td>
                      <td>
                        <Text size="sm" color="dimmed">
                          {log.model_name || '-'}
                        </Text>
                      </td>
                      <td>
                        <Spoiler
                          maxHeight={60}
                          showLabel="Show more"
                          hideLabel="Show less"
                          transitionDuration={200}
                        >
                          <div style={{ maxWidth: '400px', lineHeight: 1.5, fontSize: '0.875rem' }}>
                            {formatDescription(log.description).map((part, idx) => (
                              <div key={idx}>
                                {part}
                              </div>
                            ))}
                          </div>
                        </Spoiler>
                      </td>
                      <td>
                        <Text size="xs" style={{ fontFamily: 'monospace' }}>
                          {log.ip_address || '-'}
                        </Text>
                      </td>
                      <td>
                        <Group spacing="xs">
                          <Text size="sm">{getStatusDisplay(log.status).icon}</Text>
                          <Badge
                            size="sm"
                            color={getStatusDisplay(log.status).color}
                            variant="filled"
                          >
                            {getStatusDisplay(log.status).label}
                          </Badge>
                        </Group>
                      </td>
                      <td>
                        <Group spacing={4}>
                          <Tooltip label="View Details">
                            <ActionIcon
                              size="sm"
                              variant="light"
                              onClick={() => handleViewDetails(log)}
                            >
                              <IconInfoCircle size={16} />
                            </ActionIcon>
                          </Tooltip>
                        </Group>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>

              {/* Pagination */}
              <Group position="apart" p="md">
                <Text size="sm" color="dimmed">
                  Showing {logs.length} of {totalCount} logs
                </Text>
                <Pagination
                  total={totalPages}
                  value={currentPage}
                  onChange={setCurrentPage}
                  size="sm"
                />
              </Group>
            </>
          )}
        </Paper>

        {/* Detail Modal */}
        <Modal
          opened={detailModalOpen}
          onClose={() => setDetailModalOpen(false)}
          title={<Text weight={500}>Audit Log Details</Text>}
          size="lg"
        >
          {selectedLog && (
            <Stack spacing="md">
              <Group grow>
                <div>
                  <Text size="xs" color="dimmed" weight={500} mb={4}>
                    Timestamp
                  </Text>
                  <Text size="sm">{formatTimestamp(selectedLog.timestamp)}</Text>
                </div>
                <div>
                  <Text size="xs" color="dimmed" weight={500} mb={4}>
                    Status
                  </Text>
                  <Group spacing="xs">
                    <Text>{getStatusDisplay(selectedLog.status).icon}</Text>
                    <Badge
                      size="sm"
                      color={getStatusDisplay(selectedLog.status).color}
                      variant="filled"
                    >
                      {getStatusDisplay(selectedLog.status).label}
                    </Badge>
                  </Group>
                </div>
              </Group>

              <Group grow>
                <div>
                  <Text size="xs" color="dimmed" weight={500} mb={4}>
                    User
                  </Text>
                  <Text size="sm" weight={500}>
                    {selectedLog.user_username || 'System'}
                  </Text>
                </div>
                <div>
                  <Text size="xs" color="dimmed" weight={500} mb={4}>
                    Action
                  </Text>
                  <Badge
                    size="sm"
                    color={getActionBadgeColor(selectedLog.action)}
                    variant="light"
                  >
                    {selectedLog.action.replace(/_/g, ' ')}
                  </Badge>
                </div>
              </Group>

              <div>
                <Text size="xs" color="dimmed" weight={500} mb={4}>
                  Model
                </Text>
                <Text size="sm">{selectedLog.model_name || 'N/A'}</Text>
              </div>

              <div>
                <Text size="xs" color="dimmed" weight={500} mb={4}>
                  Description
                </Text>
                <Paper withBorder p="sm" radius="sm" style={{ backgroundColor: '#f8f9fa' }}>
                  <Text size="sm" style={{ lineHeight: 1.6, whiteSpace: 'pre-line' }}>
                    {selectedLog.description}
                  </Text>
                </Paper>
              </div>

              <Group grow>
                <div>
                  <Text size="xs" color="dimmed" weight={500} mb={4}>
                    IP Address
                  </Text>
                  <Text size="sm" style={{ fontFamily: 'monospace' }}>
                    {selectedLog.ip_address || 'N/A'}
                  </Text>
                </div>
                <div>
                  <Text size="xs" color="dimmed" weight={500} mb={4}>
                    User Agent
                  </Text>
                  <Text size="xs" style={{ fontFamily: 'monospace' }}>
                    {selectedLog.user_agent || 'N/A'}
                  </Text>
                </div>
              </Group>

              {selectedLog.reason && (
                <div>
                  <Text size="xs" color="dimmed" weight={500} mb={4}>
                    Reason
                  </Text>
                  <Text size="sm">{selectedLog.reason}</Text>
                </div>
              )}

              {selectedLog.object_id && (
                <div>
                  <Text size="xs" color="dimmed" weight={500} mb={4}>
                    Object ID
                  </Text>
                  <Code size="sm">{selectedLog.object_id}</Code>
                </div>
              )}
            </Stack>
          )}
        </Modal>
      </Stack>
    </Container>
  );
}

export default AuditLogViewerPage;
