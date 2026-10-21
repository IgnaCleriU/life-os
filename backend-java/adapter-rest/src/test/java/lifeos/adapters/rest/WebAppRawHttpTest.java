package lifeos.adapters.rest;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.SpringBootTest.WebEnvironment;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

/**
 * HTTP crudo contra Tomcat de verdad (MockMvc se salta su normalización de
 * rutas): los trucos de path no deben llegar a la API sin token ni devolver
 * la web, y los redirects salen con Location relativo.
 */
@SpringBootTest(
        webEnvironment = WebEnvironment.RANDOM_PORT,
        properties = "lifeos.api.allowed-hosts=machine.tailnet.ts.net")
class WebAppRawHttpTest {

    private static final Path TMP = tempDir();

    @Value("${local.server.port}")
    private int port;

    @DynamicPropertySource
    static void databaseUrl(DynamicPropertyRegistry registry) {
        registry.add("lifeos.database-url", () -> "jdbc:sqlite:" + TMP.resolve("raw.db"));
    }

    @Test
    void traversalTricksNeverReachTheApiOrTheWeb() throws IOException {
        // Observado con Tomcat: ..; y %2e%2e se normalizan a /projects (401 sin
        // token); %2f en el path lo rechaza Tomcat (400); /app/../projects
        // se normaliza a /projects y la guardia lo ve sin normalizar (401).
        assertRejected("/app/..;/projects", "401");
        assertRejected("/app/%2e%2e/projects", "401");
        assertRejected("/app/..%2fprojects", "400");
        assertRejected("/app/../projects", "401");
        assertRejected("/app/%2E%2E/projects", "401");
        assertRejected("/app/..%2Fprojects", "400");
        assertRejected("/app/%252e%252e/projects", "401");
    }

    @Test
    void encodedDeepLinksAreServed() throws IOException {
        for (String path : new String[] {"/app/proyectos/Casa%20nueva", "/app/a%C3%B1"}) {
            String response = raw(path, "localhost");
            assertThat(response).as(path).startsWith("HTTP/1.1 200").contains("<div id=\"root\">");
        }
    }

    @Test
    void redirectsUseARelativeLocation() throws IOException {
        for (String path : new String[] {"/", "/app"}) {
            String response = raw(path, "machine.tailnet.ts.net");
            assertThat(response).startsWith("HTTP/1.1 302");
            assertThat(response).contains("Location: /app/\r\n").doesNotContain("http://");
        }
    }

    private void assertRejected(String path, String status) throws IOException {
        String response = raw(path, "localhost");
        assertThat(response).as(path).startsWith("HTTP/1.1 " + status);
        assertThat(response).as(path).doesNotContain("<div id=\"root\">").doesNotContain("\"items\"");
    }

    private String raw(String path, String host) throws IOException {
        try (Socket socket = new Socket("127.0.0.1", port)) {
            socket.getOutputStream().write(("GET " + path + " HTTP/1.1\r\nHost: " + host
                    + "\r\nConnection: close\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
            return new String(socket.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private static Path tempDir() {
        try {
            return Files.createTempDirectory("lifeos-raw-test");
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
