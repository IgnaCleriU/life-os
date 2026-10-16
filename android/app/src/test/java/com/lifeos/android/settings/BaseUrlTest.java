package com.lifeos.android.settings;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;

import org.junit.Test;

public class BaseUrlTest {

    @Test
    public void keepsCleanHttpsUrl() {
        assertEquals("https://lifeos-vps.tail1234.ts.net", BaseUrl.normalize("https://lifeos-vps.tail1234.ts.net"));
    }

    @Test
    public void stripsTrailingSlashes() {
        assertEquals("https://host.ts.net", BaseUrl.normalize("https://host.ts.net/"));
        assertEquals("https://host.ts.net", BaseUrl.normalize("https://host.ts.net///"));
    }

    @Test
    public void addsHttpsWhenSchemeIsMissing() {
        assertEquals("https://host.ts.net", BaseUrl.normalize("host.ts.net"));
        assertEquals("https://host.ts.net:8443", BaseUrl.normalize("host.ts.net:8443/"));
    }

    @Test
    public void trimsWhitespaceAndLowercasesHost() {
        assertEquals("https://host.ts.net", BaseUrl.normalize("  HTTPS://Host.TS.net/ \n"));
    }

    @Test
    public void keepsExplicitHttpAndPathPrefix() {
        assertEquals("http://10.0.2.2:8000", BaseUrl.normalize("http://10.0.2.2:8000"));
        assertEquals("https://host.ts.net/lifeos", BaseUrl.normalize("host.ts.net/lifeos/"));
    }

    @Test
    public void rejectsEmptyAndInvalidInput() {
        for (String bad : new String[] {null, "", "   ", "ftp://host", "https://", "http://host?x=1", "https://host/#frag"}) {
            try {
                BaseUrl.normalize(bad);
                fail("Expected rejection of: " + bad);
            } catch (IllegalArgumentException expected) {
                // ok
            }
        }
    }
}
