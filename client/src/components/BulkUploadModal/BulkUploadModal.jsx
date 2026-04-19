import React, { useState } from 'react';
import {
    Modal, Stack, Group, Text, Progress, Badge, Alert, ScrollArea,
    Paper, Tooltip, ActionIcon, Box, LoadingOverlay, Button
} from '@mantine/core';
import { IconUpload, IconFileDownload, IconAlertTriangle, IconCheck, IconX, IconInfoCircle } from '@tabler/icons-react';
import { showErrorNotification, showSuccessNotification } from '../../utils/errorHandler';
import { getStandardErrorMessage } from '../../utils/erpMessages';

const BulkUploadModal = ({ opened, onClose, onUpload, onDownloadSample }) => {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [result, setResult] = useState(null);
    const [dragActive, setDragActive] = useState(false);

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            validateAndSetFile(e.dataTransfer.files[0]);
        }
    };

    const validateAndSetFile = (selectedFile) => {
        // File extension validation
        if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
            const errorMsg = getStandardErrorMessage('INVALID_FILE_TYPE');
            showErrorNotification({
                response: {
                    data: {
                        error: errorMsg.title,
                        message: errorMsg.message,
                        suggestion: errorMsg.suggestion
                    }
                }
            }, 'Invalid File Type');
            return;
        }

        // File size validation (5MB)
        const maxSize = 5 * 1024 * 1024;
        if (selectedFile.size > maxSize) {
            const sizeMB = (selectedFile.size / (1024 * 1024)).toFixed(2);
            const errorMsg = getStandardErrorMessage('DATA_TOO_LARGE', {
                value: `${sizeMB}MB (max 5MB)`
            });
            showErrorNotification({
                response: {
                    data: {
                        error: errorMsg.title,
                        message: errorMsg.message,
                        suggestion: errorMsg.suggestion
                    }
                }
            }, 'File Too Large');
            return;
        }

        setFile(selectedFile);
        setResult(null);
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setUploadProgress(0);

        // Simulate progress
        const progressInterval = setInterval(() => {
            setUploadProgress(prev => Math.min(prev + 10, 90));
        }, 200);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await onUpload(formData);

            clearInterval(progressInterval);
            setUploadProgress(100);

            setResult(response);

            if (response.success) {
                const successMsg = response.summary
                    ? `${response.summary.created} users created, ${response.summary.failed} failed`
                    : response.message;
                showSuccessNotification(successMsg, 'Upload Complete');

                // Download failed users if any
                if (response.skipped_users_count > 0 && response.skipped_users_csv) {
                    const csvUrl = URL.createObjectURL(
                        new Blob([response.skipped_users_csv], { type: 'text/csv' })
                    );
                    const a = document.createElement('a');
                    a.href = csvUrl;
                    a.download = `failed_users_${new Date().getTime()}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    URL.revokeObjectURL(csvUrl);
                }
            }
        } catch (error) {
            clearInterval(progressInterval);
            setUploadProgress(0);

            showErrorNotification(error, 'Upload Failed');

            setResult({
                success: false,
                error: error.response?.data?.error || error.response?.data?.detail || error.message,
                detail: error.response?.data
            });
        } finally {
            setUploading(false);
            clearInterval(progressInterval);
        }
    };

    const handleClose = () => {
        setFile(null);
        setResult(null);
        setUploadProgress(0);
        onClose();
    };

    const getValidationSummary = () => {
        if (!result || !result.validation_errors) return null;

        const errors = result.validation_errors;
        const errorTypes = {};

        errors.forEach(err => {
            errorTypes[err.error] = (errorTypes[err.error] || 0) + 1;
        });

        return (
            <Stack spacing="xs" mt="md">
                <Text weight={500}>Validation Errors Summary:</Text>
                {Object.entries(errorTypes).map(([type, count]) => (
                    <Group key={type} position="apart">
                        <Text size="sm">{type.replace(/_/g, ' ')}</Text>
                        <Badge color="red">{count}</Badge>
                    </Group>
                ))}
            </Stack>
        );
    };

    return (
        <Modal
            opened={opened}
            onClose={handleClose}
            title={<Text weight={600}>Bulk Upload Users</Text>}
            size="lg"
            centered
        >
            <Stack>
                {/* File Upload Area */}
                <Paper
                    p="xl"
                    withBorder
                    sx={{
                        borderStyle: 'dashed',
                        borderColor: dragActive ? '#228be6' : '#dee2e6',
                        backgroundColor: dragActive ? '#f8f9fa' : 'white',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                    }}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('file-input').click()}
                >
                    <input
                        id="file-input"
                        type="file"
                        accept=".csv"
                        style={{ display: 'none' }}
                        onChange={(e) => {
                            if (e.target.files[0]) {
                                validateAndSetFile(e.target.files[0]);
                            }
                        }}
                        disabled={uploading}
                    />

                    <Stack align="center" spacing="xs">
                        <IconUpload size={48} color="#228be6" />
                        <Text weight={500}>
                            {dragActive ? 'Drop your CSV file here' : 'Drag & drop CSV file or click to browse'}
                        </Text>
                        <Text size="sm" color="dimmed">
                            Maximum file size: 5MB | Maximum records: 1000
                        </Text>
                    </Stack>
                </Paper>

                {/* Selected File Info */}
                {file && !result && (
                    <Paper p="sm" withBorder>
                        <Group position="apart">
                            <Group spacing="xs">
                                <IconFileDownload size={20} color="#228be6" />
                                <Text size="sm">{file.name}</Text>
                                <Badge size="xs">
                                    {(file.size / 1024).toFixed(2)} KB
                                </Badge>
                            </Group>
                            <ActionIcon
                                color="red"
                                variant="light"
                                size="sm"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setFile(null);
                                }}
                                disabled={uploading}
                            >
                                <IconX size={14} />
                            </ActionIcon>
                        </Group>
                    </Paper>
                )}

                {/* Progress Bar */}
                {uploading && (
                    <Stack spacing="xs">
                        <Group position="apart">
                            <Text size="sm">Uploading and processing...</Text>
                            <Text size="sm" color="dimmed">{uploadProgress}%</Text>
                        </Group>
                        <Progress value={uploadProgress} color="blue" animate />
                    </Stack>
                )}

                {/* Results */}
                {result && !uploading && (
                    <LoadingOverlay visible={uploading} />
                )}

                {result && result.success && (
                    <Stack spacing="md">
                        <Alert icon={<IconCheck size={20} />} color="green" title="Upload Successful">
                            {result.message}
                        </Alert>

                        {result.summary && (
                            <Paper p="md" withBorder>
                                <Stack spacing="sm">
                                    <Group position="apart">
                                        <Text weight={500}>Summary</Text>
                                        <Badge color="green">
                                            {result.summary.success_rate}
                                        </Badge>
                                    </Group>
                                    <Group position="apart">
                                        <Text size="sm">Total Rows:</Text>
                                        <Text size="sm" weight={500}>{result.summary.total_rows}</Text>
                                    </Group>
                                    <Group position="apart">
                                        <Text size="sm" c="green">Created:</Text>
                                        <Text size="sm" weight={500} c="green">{result.summary.created}</Text>
                                    </Group>
                                    <Group position="apart">
                                        <Text size="sm" c="red">Failed:</Text>
                                        <Text size="sm" weight={500} c="red">{result.summary.failed}</Text>
                                    </Group>
                                </Stack>
                            </Paper>
                        )}

                        {result.validation_errors && result.validation_errors.length > 0 && (
                            <Paper p="md" withBorder>
                                {getValidationSummary()}
                            </Paper>
                        )}

                        {result.skipped_users_count > 0 && (
                            <Alert icon={<IconInfoCircle size={20} />} color="orange">
                                Failed users have been downloaded as CSV file. Please fix the errors and re-upload.
                            </Alert>
                        )}

                        {/* Created Users List */}
                        {result.created_users && result.created_users.length > 0 && (
                            <Paper p="md" withBorder>
                                <Text weight={500} mb="xs">Successfully Created Users ({result.created_users.length})</Text>
                                <ScrollArea.Autosize mah={200}>
                                    <Stack spacing="xs">
                                        {result.created_users.map((user, idx) => (
                                            <Group key={idx} position="apart" p="xs" sx={{ borderBottom: '1px solid #eee' }}>
                                                <Text size="sm">{user.username}</Text>
                                                <Badge size="xs" color="green">Row {user.row}</Badge>
                                            </Group>
                                        ))}
                                    </Stack>
                                </ScrollArea.Autosize>
                            </Paper>
                        )}
                    </Stack>
                )}

                {result && !result.success && (
                    <Alert icon={<IconAlertTriangle size={20} />} color="red" title="Upload Failed">
                        <Stack spacing="xs">
                            <Text>{result.error}</Text>
                            {result.detail && (
                                <Text size="sm" color="dimmed">{result.detail}</Text>
                            )}
                        </Stack>
                    </Alert>
                )}

                {/* Action Buttons */}
                <Group position="apart">
                    <Button
                        variant="light"
                        leftSection={<IconFileDownload size={16} />}
                        onClick={onDownloadSample}
                        disabled={uploading}
                    >
                        Download Sample CSV
                    </Button>

                    <Group>
                        <Button
                            variant="default"
                            onClick={handleClose}
                            disabled={uploading}
                        >
                            {result && result.success ? 'Done' : 'Cancel'}
                        </Button>
                        <Button
                            onClick={handleUpload}
                            disabled={!file || uploading || (result && result.success)}
                            loading={uploading}
                        >
                            {uploading ? 'Uploading...' : 'Upload'}
                        </Button>
                    </Group>
                </Group>
            </Stack>
        </Modal>
    );
};

export default BulkUploadModal;
