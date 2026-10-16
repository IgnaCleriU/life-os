package lifeos.adapters.rest;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

/**
 * Solo se atienden requests dirigidos a localhost, igual que {@code auth.py}
 * en Python. Escuchar en loopback no alcanza: con DNS rebinding, una página
 * de {@code evil.example} resuelve a 127.0.0.1 y lee la API, pero su Host
 * sigue siendo {@code evil.example}.
 */
class HostGuardTest extends RestTestSupport {

    @ParameterizedTest
    @ValueSource(strings = {"localhost", "localhost:8000", "127.0.0.1:8000", "[::1]:8000", "LOCALHOST"})
    void loopbackHostsAreServed(String host) throws Exception {
        mvc.perform(get("/projects").header("Host", host)).andExpect(status().isOk());
    }

    @ParameterizedTest
    @ValueSource(strings = {"evil.example", "evil.example:8000", "localhost.evil.example", "192.168.0.10:8000", ""})
    void otherHostsAreForbidden(String host) throws Exception {
        mvc.perform(get("/projects").header("Host", host))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.error.code").value("forbidden_host"));
    }

    @Test
    void forbiddenHostCannotWrite() throws Exception {
        String project = createProject("P");

        mvc.perform(post("/projects/" + project + "/archive").header("Host", "evil.example"))
                .andExpect(status().isForbidden());
        mvc.perform(get("/projects/" + project)).andExpect(jsonPath("$.status").value("active"));
    }

    @Test
    void healthIsOpenToAnyHost() throws Exception {
        mvc.perform(get("/health").header("Host", "evil.example")).andExpect(status().isOk());
    }
}
