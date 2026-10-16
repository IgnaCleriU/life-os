package lifeos.adapters.rest;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.net.URI;
import java.util.Locale;
import java.util.Set;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Solo atiende requests dirigidos a localhost, como {@code auth.py} en Python.
 *
 * <p>Escuchar en loopback no alcanza: con DNS rebinding, una página de
 * {@code evil.example} hace que su dominio resuelva a 127.0.0.1 y puede leer la
 * API, pero el header {@code Host} sigue diciendo {@code evil.example}. El token
 * Bearer del daemon (ADR 0009) todavía no está portado.
 */
@Component
class HostGuardFilter extends OncePerRequestFilter {

    private static final Set<String> LOOPBACK_HOSTS = Set.of("localhost", "127.0.0.1", "::1");
    private static final Set<String> OPEN_PATHS = Set.of("/health");

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return OPEN_PATHS.contains(request.getRequestURI());
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        // Sin header (HTTP/1.0; en HTTP/1.1 Tomcat ya lo rechaza) vale el nombre
        // del servidor. Un ataque de rebinding siempre manda su propio Host.
        String header = request.getHeader(HttpHeaders.HOST);
        String host = hostname(header == null ? request.getServerName() : header);
        if (host != null && LOOPBACK_HOSTS.contains(host)) {
            chain.doFilter(request, response);
            return;
        }
        response.setStatus(HttpStatus.FORBIDDEN.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.getWriter().write("{\"error\":{\"code\":\"forbidden_host\","
                + "\"message\":\"The API only answers requests addressed to localhost.\"}}");
    }

    /** Nombre de host de un header {@code Host}, con o sin puerto; null si no se puede leer. */
    static String hostname(String hostHeader) {
        if (hostHeader == null || hostHeader.isEmpty()) {
            return null;
        }
        try {
            String host = URI.create("//" + hostHeader).getHost();
            if (host == null) {
                return null;
            }
            if (host.startsWith("[") && host.endsWith("]")) {
                host = host.substring(1, host.length() - 1);
            }
            return host.toLowerCase(Locale.ROOT);
        } catch (IllegalArgumentException e) {
            return null;
        }
    }
}
