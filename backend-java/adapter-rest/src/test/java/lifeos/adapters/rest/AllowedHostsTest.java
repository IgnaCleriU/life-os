package lifeos.adapters.rest;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.test.context.TestPropertySource;

/**
 * Un VPS detrás de {@code tailscale serve} recibe {@code Host: lifeos-vps...}
 * (ADR 0010). Esos nombres se suman a loopback; el token se sigue exigiendo.
 * El valor se escribe sucio a propósito: espacios, mayúsculas, punto final, vacíos.
 */
@TestPropertySource(properties = "lifeos.api.allowed-hosts= lifeos-vps , VPS.tailnet.ts.net. ,,")
class AllowedHostsTest extends RestTestSupport {

    @ParameterizedTest
    @ValueSource(strings = {"lifeos-vps", "LIFEOS-VPS", "vps.tailnet.ts.net:443", "vps.tailnet.ts.net", "vps.tailnet.ts.net.", "localhost."})
    void configuredHostsAreServed(String host) throws Exception {
        mvc.perform(get("/projects").header("Host", host)).andExpect(status().isOk());
    }

    @Test
    void loopbackIsStillServed() throws Exception {
        mvc.perform(get("/projects").header("Host", "localhost:8000")).andExpect(status().isOk());
    }

    @ParameterizedTest
    @ValueSource(strings = {"evil.example", "lifeos-vps.evil.example", "tailnet.ts.net"})
    void otherHostsAreStillForbidden(String host) throws Exception {
        mvc.perform(get("/projects").header("Host", host))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.error.code").value("forbidden_host"));
    }

    @Test
    void configuredHostsStillNeedTheToken() throws Exception {
        anonymousMvc().perform(get("/projects").header("Host", "lifeos-vps")).andExpect(status().isUnauthorized());
    }
}
