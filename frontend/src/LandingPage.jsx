import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

const LandingContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  width: 100%;
`;

const HeroSection = styled.div`
  min-height: 85vh;
  background: linear-gradient(135deg, ${props => props.theme.colors.primary} 0%, #006666 100%);
  color: ${props => props.theme.colors.white};
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  position: relative;
  overflow: hidden;
  padding: 20px;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: url('https://images.unsplash.com/photo-1560518883-ce09059eeffa?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1673&q=80');
    background-size: cover;
    background-position: center;
    opacity: 0.2;
    z-index: 0;
  }
`;

const HeroContent = styled.div`
  max-width: 800px;
  padding: 0 20px;
  position: relative;
  z-index: 1;
`;

const Title = styled.h1`
  font-size: 3.5rem;
  margin-bottom: 1rem;
  font-weight: 700;
  
  @media (max-width: 768px) {
    font-size: 2.5rem;
  }
`;

const Subtitle = styled.h2`
  font-size: 1.5rem;
  margin-bottom: 2rem;
  font-weight: 400;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  
  @media (max-width: 768px) {
    font-size: 1.2rem;
  }
`;

const ButtonContainer = styled.div`
  display: flex;
  gap: 20px;
  margin-top: 2rem;
  justify-content: center;
  
  @media (max-width: 600px) {
    flex-direction: column;
    align-items: center;
    width: 100%;
    max-width: 300px;
  }
`;

const Button = styled(Link)`
  padding: 0.8rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 5px;
  text-decoration: none;
  text-align: center;
  transition: all 0.3s ease;
  min-width: 150px;
  
  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
  }
  
  @media (max-width: 600px) {
    width: 100%;
  }
`;

const PrimaryButton = styled(Button)`
  background-color: #ff6b6b;
  color: ${props => props.theme.colors.white};
  border: none;
  
  &:hover {
    background-color: #ff5252;
  }
`;

const SecondaryButton = styled(Button)`
  background-color: transparent;
  color: ${props => props.theme.colors.white};
  border: 2px solid ${props => props.theme.colors.white};
  
  &:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }
`;

const FeaturesSection = styled.div`
  padding: 80px 20px;
  background-color: ${props => props.theme.colors.background};
`;

const FeaturesContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`;

const FeaturesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 40px;
  margin-top: 60px;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 30px;
  }
`;

const FeatureCard = styled.div`
  background: ${props => props.theme.colors.white};
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease;
  
  &:hover {
    transform: translateY(-10px);
  }
`;

const FeatureIcon = styled.div`
  font-size: 2.5rem;
  margin-bottom: 20px;
  color: ${props => props.theme.colors.primary};
`;

const FeatureTitle = styled.h3`
  font-size: 1.5rem;
  margin-bottom: 15px;
  color: ${props => props.theme.colors.black};
`;

const FeatureDescription = styled.p`
  color: #666;
  line-height: 1.6;
`;

const SectionTitle = styled.h2`
  font-size: 2.5rem;
  text-align: center;
  color: ${props => props.theme.colors.black};
  margin-bottom: 20px;
  
  @media (max-width: 768px) {
    font-size: 2rem;
  }
`;

const SectionDescription = styled.p`
  font-size: 1.1rem;
  text-align: center;
  color: #666;
  max-width: 800px;
  margin: 0 auto 40px;
  line-height: 1.6;
  
  @media (max-width: 768px) {
    font-size: 1rem;
  }
`;

const Footer = styled.footer`
  background-color: #333;
  color: ${props => props.theme.colors.white};
  padding: 40px 20px;
  text-align: center;
`;

const FooterContent = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`;

const Copyright = styled.p`
  margin-top: 20px;
  opacity: 0.7;
  font-size: 0.9rem;
`;

const LandingPage = () => {
  return (
    <LandingContainer>
      <HeroSection>
        <HeroContent>
          <Title>TrustRent</Title>
          <Subtitle>
            A blockchain-based property management system ensuring trust, transparency, and security for all property transactions.
          </Subtitle>
          <ButtonContainer>
            <PrimaryButton to="/register">Register</PrimaryButton>
            <SecondaryButton to="/login">Login</SecondaryButton>
          </ButtonContainer>
        </HeroContent>
      </HeroSection>
      
      <FeaturesSection>
        <FeaturesContainer>
          <SectionTitle>Why Choose TrustRent?</SectionTitle>
          <SectionDescription>
            Our blockchain-powered platform revolutionizes property management with unmatched security and transparency.
          </SectionDescription>
          
          <FeaturesGrid>
            <FeatureCard>
              <FeatureIcon>🔒</FeatureIcon>
              <FeatureTitle>Secure Ownership Verification</FeatureTitle>
              <FeatureDescription>
                Verify property ownership with blockchain technology, eliminating fraud and providing unalterable proof of ownership.
              </FeatureDescription>
            </FeatureCard>
            
            <FeatureCard>
              <FeatureIcon>🔄</FeatureIcon>
              <FeatureTitle>Transparent Transactions</FeatureTitle>
              <FeatureDescription>
                Every transaction is recorded on the blockchain, creating an immutable history that anyone can verify.
              </FeatureDescription>
            </FeatureCard>
            
            <FeatureCard>
              <FeatureIcon>📝</FeatureIcon>
              <FeatureTitle>Smart Rental Agreements</FeatureTitle>
              <FeatureDescription>
                Create, sign, and manage rental agreements with built-in verification and enforcement mechanisms.
              </FeatureDescription>
            </FeatureCard>
            
            <FeatureCard>
              <FeatureIcon>👥</FeatureIcon>
              <FeatureTitle>Multi-Role Platform</FeatureTitle>
              <FeatureDescription>
                Purpose-built features for property owners, seekers, land representatives, and administrators.
              </FeatureDescription>
            </FeatureCard>
            
            <FeatureCard>
              <FeatureIcon>🔍</FeatureIcon>
              <FeatureTitle>Property History</FeatureTitle>
              <FeatureDescription>
                Access the complete history of any registered property, including ownership changes and rental history.
              </FeatureDescription>
            </FeatureCard>
            
            <FeatureCard>
              <FeatureIcon>🛡️</FeatureIcon>
              <FeatureTitle>Enhanced Security</FeatureTitle>
              <FeatureDescription>
                Multi-factor authentication and blockchain verification protect your property data and transactions.
              </FeatureDescription>
            </FeatureCard>
          </FeaturesGrid>
        </FeaturesContainer>
      </FeaturesSection>
      
      <Footer>
        <FooterContent>
          <SectionTitle style={{ color: 'white', fontSize: '1.8rem' }}>TrustRent</SectionTitle>
          <Copyright>© {new Date().getFullYear()} TrustRent. All rights reserved.</Copyright>
        </FooterContent>
      </Footer>
    </LandingContainer>
  );
};

export default LandingPage; 