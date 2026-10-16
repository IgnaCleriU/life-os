package lifeos.adapters.rest;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.test.web.servlet.MockMvc;

/**
 * La web (build de {@code frontend/}) se sirve en {@code /app/} desde el mismo
 * origen que la API, sin token: el navegador la carga y recién después llama a
 * la API con el bearer. Usa un {@code static/app/} falso de los test resources.
 */
class WebAppTest extends RestTestSupport {

    @Test
    void indexIsServedWithoutToken() throws Exception {
        anonymousMvc().perform(get("/app/"))
                .andExpect(status().isOk())
                .andExpect(content().string(containsString("<div id=\"root\">")))
                .andExpect(header().string("Cache-Control", "no-cache"));
    }

    @Test
    void rootAndAppRedirectToAppSlash() throws Exception {
        for (String path : new String[] {"/", "/app"}) {
            anonymousMvc().perform(get(path))
                    .andExpect(status().is3xxRedirection())
                    .andExpect(redirectedUrl("/app/"));
        }
    }

    @Test
    void assetsAreImmutableAndNeedNoToken() throws Exception {
        anonymousMvc().perform(get("/app/assets/test-app.js"))
                .andExpect(status().isOk())
                .andExpect(content().string(containsString("life-os test")))
                .andExpect(header().string("Cache-Control", "max-age=31536000, public, immutable"));
    }

    @ParameterizedTest
    @ValueSource(strings = {"/app/projects", "/app/projects/123/tasks", "/app/index.html", "/app/anything.txt"})
    void clientSideRoutesFallBackToIndex(String path) throws Exception {
        anonymousMvc().perform(get(path))
                .andExpect(status().isOk())
                .andExpect(content().string(containsString("<div id=\"root\">")))
                .andExpect(header().string("Cache-Control", "no-cache"));
    }

    @ParameterizedTest
    @ValueSource(strings = {"/app/proyectos/Casa%20nueva", "/app/a%C3%B1/b", "/app/x%2Dy"})
    void encodedDeepLinksFallBackToIndex(String path) throws Exception {
        // URI.create: con un String, MockMvc volvería a codificar el %.
        anonymousMvc().perform(get(java.net.URI.create(path)))
                .andExpect(status().isOk())
                .andExpect(content().string(containsString("<div id=\"root\">")));
    }

    @Autowired
    private org.springframework.web.servlet.HandlerMapping resourceHandlerMapping;

    /** Un CachingResourceResolver guardaría una entrada por cada /app/<ruta> distinta (memoria sin tope). */
    @Test
    void spaFallbackIsNotCached() {
        var handler = (org.springframework.web.servlet.resource.ResourceHttpRequestHandler)
                ((org.springframework.web.servlet.handler.SimpleUrlHandlerMapping) resourceHandlerMapping)
                        .getUrlMap().get("/app/**");
        org.assertj.core.api.Assertions.assertThat(handler.getResourceResolvers())
                .noneMatch(r -> r instanceof org.springframework.web.servlet.resource.CachingResourceResolver);
    }

    @ParameterizedTest
    @ValueSource(strings = {"/app/assets/missing.js", "/app/assets/", "/app/assets", "/app/assets/sub/missing.css"})
    void missingAssetsAre404NotHtml(String path) throws Exception {
        anonymousMvc().perform(get(path))
                .andExpect(status().isNotFound())
                .andExpect(content().string(org.hamcrest.Matchers.not(containsString("<div id=\"root\">"))))
                .andExpect(header().doesNotExist("Cache-Control"));
    }

    @ParameterizedTest
    @ValueSource(strings = {"/app/", "/app/assets/test-app.js", "/app/projects", "/app", "/"})
    void webResponsesCarrySecurityHeaders(String path) throws Exception {
        anonymousMvc().perform(get(path))
                .andExpect(header().string("Content-Security-Policy", WebHeadersFilter.CSP))
                .andExpect(header().string("Content-Security-Policy", containsString("script-src 'self';")))
                .andExpect(header().string("Content-Security-Policy", containsString("frame-ancestors 'none'")))
                .andExpect(header().string("X-Content-Type-Options", "nosniff"))
                .andExpect(header().string("Referrer-Policy", "no-referrer"));
    }

    @Test
    void foreignHostIsForbiddenOnTheWeb() throws Exception {
        for (String path : new String[] {"/", "/app", "/app/", "/app/assets/test-app.js", "/app/projects"}) {
            anonymousMvc().perform(get(path).header("Host", "evil.example"))
                    .andExpect(status().isForbidden())
                    .andExpect(jsonPath("$.error.code").value("forbidden_host"));
        }
    }

    @Test
    void apiStillNeedsTheToken() throws Exception {
        for (String path : new String[] {"/projects", "/projects/", "/tasks"}) {
            anonymousMvc().perform(get(path)).andExpect(status().isUnauthorized());
        }
        anonymousMvc().perform(post("/projects").contentType("application/json").content("{\"name\":\"x\"}"))
                .andExpect(status().isUnauthorized());
        anonymousMvc().perform(get("/health")).andExpect(status().isOk());
    }

    @Test
    void writeMethodsOnTheWebNeedTheToken() throws Exception {
        for (String path : new String[] {"/app/x", "/app/", "/app", "/"}) {
            anonymousMvc().perform(post(path)).andExpect(status().isUnauthorized());
            anonymousMvc().perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete(path))
                    .andExpect(status().isUnauthorized());
        }
        anonymousMvc().perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.head("/app/"))
                .andExpect(status().isOk());
    }

    @Test
    void webResponsesDoNotLeakIntoTheApi() throws Exception {
        mvc.perform(get("/projects")).andExpect(status().isOk())
                .andExpect(header().doesNotExist("Content-Security-Policy"));
    }

    /** Rutas que parecen estar bajo /app pero apuntan a la API (o a otra cosa): exigen token. */
    @ParameterizedTest
    @ValueSource(strings = {
        "/app/../projects", "/app/./../projects", "/app/assets/../../projects", "/app/%2e%2e/projects",
        "/app/%2E%2E/projects", "/app%2f../projects", "/app%2f..%2fprojects", "/app/..%2fprojects",
        "/app/;/../projects", "/app;x/../projects", "/app/..;/projects", "/app\\..\\projects",
        "//projects", "/app//../projects", "//app/../projects", "/APP/", "/App/index.html",
        "/application", "/app.js", "/appx/", "/app/%2e%2e%2fprojects"
    })
    void trickyPathsAreNotTreatedAsWeb(String path) throws Exception {
        // Sin token nunca pasa a la API: 401 (o 403/400 si el host o Spring la rechazan antes; en
        // MockMvc "//projects" se lee como un host), nunca datos ni HTML de la web.
        anonymousMvc().perform(get(path))
                .andExpect(status().is(org.hamcrest.Matchers.anyOf(
                        org.hamcrest.Matchers.is(401), org.hamcrest.Matchers.is(403),
                        org.hamcrest.Matchers.is(400))))
                .andExpect(content().string(org.hamcrest.Matchers.not(containsString("<div id=\"root\">"))));
    }

    @Test
    void webPathPredicateIsStrict() {
        assertWeb("/", true);
        assertWeb("/app", true);
        assertWeb("/app/", true);
        assertWeb("/app/assets/a.js", true);
        assertWeb("/app/a.b/c", true);
        assertWeb("/app/..", false);
        assertWeb("/app/a/../b", false);
        assertWeb("/app/a%2fb", false);
        assertWeb("/app/a%2Fb", false);
        assertWeb("/app/%2E%2e/x", false);
        assertWeb("/app/a%5Cb", false);
        assertWeb("/app/a%3bb", false);
        assertWeb("/app/a%252e", false);
        assertWeb("/app/a%00", false);
        assertWeb("/app/a%", false);
        assertWeb("/app/a%zz", false);
        assertWeb("/app/proyectos/Casa%20nueva", true);
        assertWeb("/app/a%C3%B1", true);
        assertWeb("/app//x", false);
        assertWeb("/APP/", false);
        assertWeb("/projects", false);
        assertWeb("/appx", false);
    }

    private static void assertWeb(String uri, boolean expected) {
        org.springframework.mock.web.MockHttpServletRequest request =
                new org.springframework.mock.web.MockHttpServletRequest("GET", uri);
        org.assertj.core.api.Assertions.assertThat(WebPaths.isWeb(request)).as(uri).isEqualTo(expected);
    }
}
