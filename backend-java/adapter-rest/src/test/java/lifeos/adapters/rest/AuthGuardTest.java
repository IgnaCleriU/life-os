package lifeos.adapters.rest;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.options;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.http.MediaType;

/**
 * Toda ruta salvo {@code /health} exige {@code Authorization: Bearer <token>}
 * (ADR 0009/0012), como {@code test_auth.py} en Python. Estos tests usan un
 * MockMvc sin token por defecto y lo mandan a mano.
 */
class AuthGuardTest extends RestTestSupport {

    private static final String BEARER = "Bearer " + TOKEN;

    @Test
    void requestWithTheTokenPasses() throws Exception {
        anonymousMvc().perform(get("/projects").header("Authorization", BEARER)).andExpect(status().isOk());
    }

    @Test
    void missingTokenIsUnauthorized() throws Exception {
        anonymousMvc().perform(get("/projects"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error.code").value("unauthorized"))
                .andExpect(header().string("WWW-Authenticate", "Bearer"));
    }

    @Test
    void wrongTokenIsUnauthorized() throws Exception {
        anonymousMvc().perform(get("/projects").header("Authorization", "Bearer nope"))
                .andExpect(status().isUnauthorized())
                .andExpect(header().string("WWW-Authenticate", "Bearer"));
    }

    @Test
    void tokenPrefixOrSuffixIsNotEnough() throws Exception {
        anonymousMvc().perform(get("/projects").header("Authorization", BEARER + "x"))
                .andExpect(status().isUnauthorized());
        anonymousMvc().perform(get("/projects").header("Authorization", "Bearer test-toke"))
                .andExpect(status().isUnauthorized());
    }

    @ParameterizedTest
    @ValueSource(strings = {"Bearer", "bearer", "BEARER", "BeArEr"})
    void schemeIsCaseInsensitive(String scheme) throws Exception {
        anonymousMvc().perform(get("/projects").header("Authorization", scheme + " " + TOKEN))
                .andExpect(status().isOk());
    }

    @Test
    void nonBearerSchemeIsUnauthorized() throws Exception {
        anonymousMvc().perform(get("/projects").header("Authorization", "Basic " + TOKEN))
                .andExpect(status().isUnauthorized());
        anonymousMvc().perform(get("/projects").header("Authorization", TOKEN))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void nonAsciiTokenIsUnauthorizedNot500() throws Exception {
        // Tomcat decodifica los headers como latin-1, así que un "é" llega como un carácter no ASCII.
        anonymousMvc().perform(get("/projects").header("Authorization", "Bearer tokén"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void writesAreBlockedWithoutTheToken() throws Exception {
        anonymousMvc().perform(post("/projects").contentType(MediaType.APPLICATION_JSON).content("{\"name\": \"Casa\"}"))
                .andExpect(status().isUnauthorized());
        mvc.perform(get("/projects")).andExpect(status().isOk()).andExpect(jsonPath("$.length()").value(0));
    }

    @Test
    void corsPreflightIsRejectedWithoutCorsHeaders() throws Exception {
        anonymousMvc().perform(options("/projects")
                        .header("Origin", "https://evil.example")
                        .header("Access-Control-Request-Method", "POST")
                        .header("Access-Control-Request-Headers", "authorization"))
                .andExpect(status().isUnauthorized())
                .andExpect(header().doesNotExist("Access-Control-Allow-Origin"));
    }

    @Test
    void healthStaysOpen() throws Exception {
        anonymousMvc().perform(get("/health")).andExpect(status().isOk());
    }

    @Test
    void forbiddenHostWinsOverMissingToken() throws Exception {
        anonymousMvc().perform(get("/projects").header("Host", "evil.example"))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.error.code").value("forbidden_host"))
                .andExpect(header().doesNotExist("WWW-Authenticate"));
    }

    @Test
    void forbiddenHostIsRejectedEvenWithTheToken() throws Exception {
        anonymousMvc().perform(get("/projects").header("Host", "evil.example").header("Authorization", BEARER))
                .andExpect(status().isForbidden());
    }
}
