package lifeos.adapters.rest;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.test.context.TestPropertySource;

/** Auth encendida y sin token configurado: falla cerrado, como Python. */
@TestPropertySource(properties = "lifeos.api.token=")
class AuthFailClosedTest extends RestTestSupport {

    @Test
    void everyGuardedRouteIsUnauthorizedEvenWithABearer() throws Exception {
        mvc.perform(get("/projects").header("Authorization", "Bearer anything"))
                .andExpect(status().isUnauthorized())
                .andExpect(header().string("WWW-Authenticate", "Bearer"))
                .andExpect(jsonPath("$.error.code").value("unauthorized"))
                .andExpect(jsonPath("$.error.message").value(containsString("LIFEOS_API_TOKEN")));
    }

    @Test
    void guardErrorsAreUtf8Json() throws Exception {
        mvc.perform(get("/projects").header("Authorization", "Bearer anything"))
                .andExpect(header().string("Content-Type", containsString("application/json")))
                .andExpect(header().string("Content-Type", containsString("charset=UTF-8")));
    }

    @Test
    void anEmptyBearerDoesNotMatchTheMissingToken() throws Exception {
        anonymousMvc().perform(get("/projects").header("Authorization", "Bearer "))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void healthStaysOpen() throws Exception {
        mvc.perform(get("/health")).andExpect(status().isOk());
    }
}
