import React, { useState } from "react";
import { useForm } from "@mantine/form";
import { TextInput, Button, Paper, Container, Title, Text, Alert, PasswordInput } from "@mantine/core";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const LoginPage = () => {
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const form = useForm({
    initialValues: { username: "", password: "" },
    validate: {
      username: (value) => (value.length > 0 ? null : "Username or email is required"),
      password: (value) => (value.length >= 6 ? null : "Password must be at least 6 characters"),
    },
  });

  const onLogin = async (values) => {
    setError(null);
    setLoading(true);

    try {
      await login(values.username, values.password);
      navigate("/UserDirectory", { replace: true });
    } catch (error) {
      // Handle both object and string error responses
      const errorData = error.response?.data?.error;
      
      if (typeof errorData === 'object' && errorData !== null) {
        // Error is an object with message property
        setError(errorData.message || "Login failed. Please check your credentials.");
      } else if (typeof errorData === 'string') {
        // Error is a simple string
        setError(errorData);
      } else {
        // Fallback error message
        setError("Login failed. Please check your credentials.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size={500} my={40}>
      <Title align="center" order={1}>Fusion ERP System Administrator</Title>
      <Text color="dimmed" align="center" mb="md">Login to access the system</Text>

      {error && (
        <Alert color="red" mb="md" title="Login Failed">
          {error}
        </Alert>
      )}

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <form onSubmit={form.onSubmit(onLogin)}>
          <TextInput
            label="Username or Email"
            placeholder="23bcs061 or admin@iiitdmj.ac.in"
            {...form.getInputProps("username")}
            required
            disabled={loading}
          />
          <PasswordInput
            label="Password"
            placeholder="Enter your password"
            mt="md"
            {...form.getInputProps("password")}
            required
            disabled={loading}
          />
          <Button type="submit" fullWidth mt="xl" loading={loading} size="md">
            Login
          </Button>
        </form>

        <Text size="xs" color="dimmed" mt="md" align="center">
          Default: username: admin, password: Admin@123
        </Text>
      </Paper>
    </Container>
  );
};

export default LoginPage;
