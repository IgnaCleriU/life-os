package lifeos.adapters.rest;

import java.io.IOException;
import java.util.concurrent.TimeUnit;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.http.CacheControl;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.ViewControllerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.resource.PathResourceResolver;

/**
 * Sirve la web (build de {@code frontend/}) desde el classpath
 * {@code static/app/}, bajo {@code /app/}, en el mismo origen que la API.
 *
 * <ul>
 *   <li>{@code /} y {@code /app} redirigen a {@code /app/}.
 *   <li>{@code /app/assets/**}: archivos con hash, cache larga e inmutable;
 *       lo que no existe es 404 (no HTML).
 *   <li>El resto de {@code /app/**}: el archivo si existe y si no
 *       {@code index.html} (rutas del lado del cliente); sin cache.
 * </ul>
 */
@Configuration
class WebAppConfiguration implements WebMvcConfigurer {

    private static final String LOCATION = "classpath:/static/app/";

    @Override
    public void addViewControllers(ViewControllerRegistry registry) {
        registry.addRedirectViewController("/", "/app/");
        registry.addRedirectViewController("/app", "/app/");
    }

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/app/assets/**")
                .addResourceLocations(LOCATION + "assets/")
                .setCacheControl(CacheControl.maxAge(365, TimeUnit.DAYS).cachePublic().immutable());
        registry.addResourceHandler("/app/**")
                .addResourceLocations(LOCATION)
                .setCacheControl(CacheControl.noCache())
                .resourceChain(true)
                .addResolver(new SpaFallbackResolver());
    }

    /** El archivo pedido si existe; si no, {@code index.html}. */
    static class SpaFallbackResolver extends PathResourceResolver {
        @Override
        protected Resource getResource(String resourcePath, Resource location) throws IOException {
            Resource found = resourcePath.isEmpty() || resourcePath.equals("/")
                    ? null
                    : super.getResource(resourcePath, location);
            // Un directorio no es legible, así que cae al index.
            if (found != null && found.isReadable()) {
                return found;
            }
            Resource index = new ClassPathResource("static/app/index.html");
            return index.exists() ? index : null;
        }
    }
}
