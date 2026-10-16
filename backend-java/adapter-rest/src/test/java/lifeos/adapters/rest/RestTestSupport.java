package lifeos.adapters.rest;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.jayway.jsonpath.JsonPath;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.BeforeEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;

/**
 * Base de los tests REST: la app completa contra una base SQLite en un
 * directorio temporal, vaciada antes de cada test. Nunca la base real.
 */
@SpringBootTest
@AutoConfigureMockMvc
abstract class RestTestSupport {

    private static final Path TMP = createTempDir();

    @Autowired
    protected MockMvc mvc;

    @Autowired
    private JdbcClient jdbc;

    @Value("${lifeos.database-url}")
    private String databaseUrl;

    @DynamicPropertySource
    static void databaseUrl(DynamicPropertyRegistry registry) {
        registry.add("lifeos.database-url", () -> "jdbc:sqlite:" + TMP.resolve("rest.db"));
    }

    /**
     * Vacía la base antes de cada test, pero primero verifica que sea la
     * temporal: si la propiedad no llegara, la app abriría la base real del
     * usuario y estos DELETE borrarían datos personales.
     */
    @BeforeEach
    void emptyDatabase() {
        if (!databaseUrl.startsWith("jdbc:sqlite:" + TMP)) {
            throw new IllegalStateException("Los tests REST no apuntan a la base temporal: " + databaseUrl);
        }
        jdbc.sql("DELETE FROM tasks").update();
        jdbc.sql("DELETE FROM projects").update();
    }

    protected String createProject(String name) throws Exception {
        return idOf(postJson("/projects", "{\"name\": \"" + name + "\"}"));
    }

    protected String createTask(String projectId, String json) throws Exception {
        return idOf(postJson("/projects/" + projectId + "/tasks", json));
    }

    protected String postJson(String url, String json) throws Exception {
        return mvc.perform(post(url).contentType(MediaType.APPLICATION_JSON).content(json))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
    }

    protected static String idOf(String json) {
        return JsonPath.read(json, "$.id");
    }

    private static Path createTempDir() {
        try {
            return Files.createTempDirectory("lifeos-rest-test");
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
