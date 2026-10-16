package lifeos.adapters.rest;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.test.context.TestPropertySource;

/**
 * {@code LIFEOS_API_AUTH=disabled} apaga la guardia entera, host incluido,
 * igual que {@code create_app(auth_enabled=False)} en Python. Solo para desarrollo.
 */
@TestPropertySource(properties = "lifeos.api.auth=disabled")
class AuthDisabledTest extends RestTestSupport {

    @Test
    void noTokenIsNeeded() throws Exception {
        anonymousMvc().perform(get("/projects")).andExpect(status().isOk());
    }

    @Test
    void noHostCheckEither() throws Exception {
        anonymousMvc().perform(get("/projects").header("Host", "evil.example")).andExpect(status().isOk());
    }
}
